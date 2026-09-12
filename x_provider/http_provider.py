"""X/Twitter provider using direct HTTP requests (no browser).

Uses auth_token + ct0 cookies to call X's internal GraphQL API.
Works in cloud environments where Chromium is not available.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from urllib import parse

import httpx

from config import Config
from models.post import Post
from x_provider.provider import XProvider

# X GraphQL endpoint for Search Timeline
SEARCH_URL = "https://x.com/i/api/graphql/lZ0GCEojmtW5TyRyx14BQA/SearchTimeline"

# Features for GraphQL query
FEATURES = {
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "tweetypie_unmention_optimization_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "articles_preview_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}


class HttpXProvider(XProvider):
    """X provider using HTTP API (no browser needed)."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        super().__init__(config, logger)
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize HTTP client with session cookies."""
        if not self.config.x_cookies_configured():
            raise RuntimeError("X cookies not configured. Set X_AUTH_TOKEN and X_CT0 in .env")

        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Referer": "https://x.com/",
                "Origin": "https://x.com",
            },
            cookies={
                "auth_token": self.config.x_auth_token or "",
                "ct0": self.config.x_ct0 or "",
            },
            follow_redirects=True,
            timeout=30,
        )
        self.logger.info("HTTP X client initialized.")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def validate_session(self) -> bool:
        """Check if X session is authenticated via HTTP."""
        try:
            if not self._client:
                return False
            # Hit a simple endpoint to check auth
            resp = await self._client.get("https://x.com/i/api/1.1/account/verify_credentials.json")
            if resp.status_code == 200:
                data = resp.json()
                screen_name = data.get("screen_name", "")
                if screen_name:
                    self.logger.info(f"X session authenticated: @{screen_name}")
                else:
                    self.logger.info("X session authenticated.")
                return True
            elif resp.status_code in (401, 403):
                self.logger.warning("X session NOT authenticated (cookies expired or invalid).")
                return False
            else:
                self.logger.warning(f"X session check returned status {resp.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error validating X session: {e}")
            return False

    async def login_flow(self) -> None:
        """Not needed for HTTP provider — cookies are set in .env."""
        self.logger.info("HTTP provider uses cookies from .env — no browser login needed.")
        print("Set X_AUTH_TOKEN and X_CT0 in .env. Run: python app.py --login")

    async def search_posts(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[Post]:
        """Search X via GraphQL API."""
        max_results = max_results or self.config.max_posts_per_query
        posts: list[Post] = []

        if not self._client:
            return posts

        self.logger.info(f"Searching (HTTP): {query}")

        cursor = ""
        pages = 0
        max_pages = (max_results // 20) + 1

        try:
            while len(posts) < max_results and pages < max_pages:
                variables = {
                    "rawQuery": query,
                    "count": min(20, max_results - len(posts)),
                    "querySource": "typed_query",
                    "product": "Latest",
                }
                if cursor:
                    variables["cursor"] = cursor

                params = {
                    "variables": parse.quote(json_dumps(variables)),
                    "features": parse.quote(json_dumps(FEATURES)),
                }

                resp = await self._client.get(SEARCH_URL, params=params)

                if resp.status_code != 200:
                    self.logger.warning(f"Search returned status {resp.status_code}")
                    break

                data = resp.json()
                new_posts, cursor = self._parse_search_response(data)

                if not new_posts:
                    break

                posts.extend(new_posts)
                pages += 1

                if not cursor:
                    break

            self.logger.info(f"Query '{query}': collected {len(posts)} posts (HTTP)")

        except Exception as e:
            self.logger.error(f"Error searching '{query}': {e}")

        return posts[:max_results]

    def _parse_search_response(self, data: dict) -> tuple[list[Post], str]:
        """Parse GraphQL search response into Post objects."""
        posts: list[Post] = []
        next_cursor = ""

        try:
            instructions = (
                data.get("data", {})
                .get("search_by_raw_query", {})
                .get("search_timeline", {})
                .get("timeline", {})
                .get("instructions", [])
            )

            for instruction in instructions:
                if instruction.get("type") == "TimelineAddEntries":
                    entries = instruction.get("entries", [])
                    for entry in entries:
                        entry_id = entry.get("entryId", "")

                        # Extract cursor for pagination
                        if entry_id.startswith("cursor-bottom"):
                            content = entry.get("content", {})
                            next_cursor = content.get("value", "")
                            continue

                        if entry_id.startswith("cursor-top"):
                            continue

                        # Parse tweet
                        tweet = self._parse_tweet_entry(entry)
                        if tweet:
                            posts.append(tweet)

        except Exception as e:
            self.logger.debug(f"Error parsing search response: {e}")

        return posts, next_cursor

    def _parse_tweet_entry(self, entry: dict) -> Post | None:
        """Parse a single tweet entry from GraphQL response."""
        try:
            content = entry.get("content", {})
            item_content = content.get("itemContent", {})
            tweet_results = item_content.get("tweet_results", {})
            result = tweet_results.get("result", {})

            if not result:
                return None

            # Handle both normal and legacy tweets
            tweet_data = result.get("legacy", result)
            core = result.get("core", {})
            user_results = core.get("user_results", {})
            user_data = user_results.get("result", {})
            user_legacy = user_data.get("legacy", user_data)

            # Extract tweet ID
            tweet_id = tweet_data.get("id_str", "") or result.get("rest_id", "")
            if not tweet_id:
                return None

            # Extract text
            text = tweet_data.get("full_text", "")
            if not text:
                return None

            # Extract author
            author_username = user_legacy.get("screen_name", "")
            author_display_name = user_legacy.get("name", None)

            # Build tweet URL
            tweet_url = f"https://x.com/{author_username}/status/{tweet_id}" if author_username else ""

            # Extract timestamp
            created_at = None
            created_str = tweet_data.get("created_at", "")
            if created_str:
                try:
                    created_at = datetime.strptime(
                        created_str, "%a %b %d %H:%M:%S %z %Y"
                    )
                except (ValueError, TypeError):
                    pass

            # Extract entities
            entities = tweet_data.get("entities", {})
            urls = []
            for url_entity in entities.get("urls", []):
                expanded = url_entity.get("expanded_url", "")
                if expanded:
                    urls.append(expanded)

            hashtags = [
                ht.get("text", "") for ht in entities.get("hashtags", [])
            ]
            mentions = [
                m.get("screen_name", "") for m in entities.get("user_mentions", [])
            ]

            return Post(
                tweet_id=tweet_id,
                author_username=author_username,
                author_display_name=author_display_name,
                text=text,
                tweet_url=tweet_url,
                created_at=created_at,
                urls=urls,
                hashtags=hashtags,
                mentions=mentions,
            )

        except Exception as e:
            self.logger.debug(f"Error parsing tweet entry: {e}")
            return None


def json_dumps(obj: dict) -> str:
    """Compact JSON encode for URL params."""
    import json
    return json.dumps(obj, separators=(",", ":"))
