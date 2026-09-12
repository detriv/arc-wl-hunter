"""X/Twitter provider using Twitter API v2 (Bearer Token).

For cloud deployment where cookies don't work (IP blocked by X).
Requires Twitter Developer account with Bearer Token.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from config import Config
from models.post import Post
from x_provider.provider import XProvider

TWITTER_API_SEARCH = "https://api.twitter.com/2/tweets/search/recent"


class TwitterApiProvider(XProvider):
    """X provider using Twitter API v2 Bearer Token."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        super().__init__(config, logger)
        self._client: httpx.AsyncClient | None = None
        self._token = config.twitter_bearer_token

    async def initialize(self) -> None:
        """Initialize HTTP client with Bearer Token."""
        if not self._token:
            raise RuntimeError("Twitter Bearer Token not configured. Set TWITTER_BEARER_TOKEN in .env")

        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self._token}",
                "User-Agent": "ArcWLHunter/1.0",
            },
            timeout=30,
        )
        self.logger.info("Twitter API client initialized.")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def validate_session(self) -> bool:
        """Check if Bearer Token is valid."""
        try:
            if not self._client:
                return False
            # Simple check: search for a known term
            resp = await self._client.get(
                TWITTER_API_SEARCH,
                params={"query": "test", "max_results": 5},
            )
            if resp.status_code == 200:
                self.logger.info("Twitter API authenticated.")
                return True
            elif resp.status_code in (401, 403):
                self.logger.warning("Twitter API: invalid or expired Bearer Token.")
                return False
            else:
                self.logger.warning(f"Twitter API check returned status {resp.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error validating Twitter API: {e}")
            return False

    async def login_flow(self) -> None:
        """Not needed for API — token is set in .env."""
        self.logger.info("API provider uses Bearer Token from .env — no login needed.")

    async def search_posts(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[Post]:
        """Search X via API v2 recent search."""
        max_results = max_results or self.config.max_posts_per_query
        posts: list[Post] = []

        if not self._client:
            return posts

        self.logger.info(f"Searching (API): {query}")

        # API v2 max is 100 per request, paginate if needed
        next_token = None
        remaining = max_results

        try:
            while remaining > 0 and len(posts) < max_results:
                batch_size = min(remaining, 100)

                params = {
                    "query": f"{query} -is:retweet",
                    "max_results": batch_size,
                    "tweet.fields": "created_at,author_id,entities,public_metrics",
                    "expansions": "author_id",
                    "user.fields": "username,name",
                }
                if next_token:
                    params["next_token"] = next_token

                resp = await self._client.get(TWITTER_API_SEARCH, params=params)

                if resp.status_code != 200:
                    self.logger.warning(f"Twitter API returned status {resp.status_code}: {resp.text[:200]}")
                    break

                data = resp.json()
                batch = self._parse_response(data)
                posts.extend(batch)

                # Check for next page
                next_token = data.get("meta", {}).get("next_token")
                remaining -= len(batch)

                if not next_token or not batch:
                    break

            self.logger.info(f"Query '{query}': collected {len(posts)} posts (API)")

        except Exception as e:
            self.logger.error(f"Error searching '{query}': {e}")

        return posts[:max_results]

    def _parse_response(self, data: dict) -> list[Post]:
        """Parse API v2 search response."""
        posts: list[Post] = []

        try:
            tweets = data.get("data", [])
            users = {
                u["id"]: u for u in data.get("includes", {}).get("users", [])
            }

            for tweet in tweets:
                tweet_id = tweet.get("id", "")
                text = tweet.get("text", "")
                author_id = tweet.get("author_id", "")
                created_str = tweet.get("created_at", "")

                user = users.get(author_id, {})
                username = user.get("username", "")
                display_name = user.get("name")

                # Parse timestamp
                created_at = None
                if created_str:
                    try:
                        created_at = datetime.fromisoformat(
                            created_str.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass

                # Extract entities
                entities = tweet.get("entities", {})
                urls = [
                    u.get("expanded_url", "")
                    for u in entities.get("urls", [])
                    if u.get("expanded_url")
                ]
                hashtags = [
                    ht.get("tag", "")
                    for ht in entities.get("hashtags", [])
                ]
                mentions = [
                    m.get("username", "")
                    for m in entities.get("mentions", [])
                ]

                tweet_url = f"https://x.com/{username}/status/{tweet_id}" if username else ""

                posts.append(Post(
                    tweet_id=tweet_id,
                    author_username=username,
                    author_display_name=display_name,
                    text=text,
                    tweet_url=tweet_url,
                    created_at=created_at,
                    urls=urls,
                    hashtags=hashtags,
                    mentions=mentions,
                ))

        except Exception as e:
            self.logger.debug(f"Error parsing API response: {e}")

        return posts
