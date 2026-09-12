"""X/Twitter provider using Nitter RSS feeds.

Nitter is an alternative Twitter frontend that exposes RSS feeds.
No API key needed. Works in cloud environments.

Note: Many public Nitter instances are down. Users can self-host or
use reliable instances.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx

from config import Config
from models.post import Post
from x_provider.provider import XProvider

DEFAULT_NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
]


class NitterProvider(XProvider):
    """X provider using Nitter RSS (no API key, no browser)."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        super().__init__(config, logger)
        self._client: httpx.AsyncClient | None = None
        self._base_url: str | None = None

    async def initialize(self) -> None:
        """Find a working Nitter instance."""
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
            follow_redirects=True,
            timeout=15,
        )

        # Try to find a working instance
        nitter_url = self.config.nitter_url
        if nitter_url:
            # User specified one
            if await self._check_instance(nitter_url):
                self._base_url = nitter_url.rstrip("/")
                return

        # Try defaults
        for url in DEFAULT_NITTER_INSTANCES:
            if await self._check_instance(url):
                self._base_url = url
                break

        if not self._base_url:
            raise RuntimeError(
                "No working Nitter instance found. "
                "Set NITTER_URL in .env to a working instance, "
                "or self-host: https://github.com/zedeus/nitter"
            )

        self.logger.info(f"Nitter instance: {self._base_url}")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _check_instance(self, url: str) -> bool:
        """Check if a Nitter instance is alive."""
        try:
            resp = await self._client.get(f"{url}/x", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    async def validate_session(self) -> bool:
        """Check if Nitter instance is reachable."""
        if not self._base_url:
            return False
        return await self._check_instance(self._base_url)

    async def login_flow(self) -> None:
        """Not needed for Nitter."""
        self.logger.info("Nitter provider needs no login. Set NITTER_URL if needed.")

    async def search_posts(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[Post]:
        """Search X via Nitter RSS."""
        max_results = max_results or self.config.max_posts_per_query
        posts: list[Post] = []

        if not self._client or not self._base_url:
            return posts

        self.logger.info(f"Searching (Nitter): {query}")

        try:
            # Nitter search RSS: /search/rss?f=tweets&q=QUERY
            search_url = f"{self._base_url}/search/rss"
            resp = await self._client.get(
                search_url,
                params={"f": "tweets", "q": query, "e-nativeretweets": "on"},
            )

            if resp.status_code != 200:
                self.logger.warning(f"Nitter returned status {resp.status_code}")
                return posts

            # Parse RSS XML
            posts = self._parse_rss(resp.text, max_results)

            self.logger.info(f"Query '{query}': collected {len(posts)} posts (Nitter)")

        except Exception as e:
            self.logger.error(f"Error searching via Nitter: {e}")

        return posts[:max_results]

    def _parse_rss(self, xml_text: str, max_results: int) -> list[Post]:
        """Parse Nitter RSS XML into Post objects."""
        posts = []

        # Simple regex parsing (no XML parser dependency)
        items = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)

        for item in items[:max_results]:
            try:
                # Extract title (tweet text)
                title_match = re.search(r"<title>(.*?)</title>", item, re.DOTALL)
                if not title_match:
                    continue
                text = self._clean_xml(title_match.group(1))
                if not text:
                    continue

                # Extract link (tweet URL)
                link_match = re.search(r"<link>(.*?)</link>", item)
                tweet_url = link_match.group(1).strip() if link_match else ""

                # Extract tweet ID from URL
                tweet_id = ""
                if "/status/" in tweet_url:
                    id_match = re.search(r"/status/(\d+)", tweet_url)
                    if id_match:
                        tweet_id = id_match.group(1)

                # Extract author
                author_match = re.search(r"<dc:creator>(.*?)</dc:creator>", item)
                author = self._clean_xml(author_match.group(1)) if author_match else ""
                author_username = author.lstrip("@") if author else ""

                # Extract description (may contain more text)
                desc_match = re.search(r"<description>(.*?)</description>", item, re.DOTALL)
                description = self._clean_xml(desc_match.group(1)) if desc_match else ""

                # Use description if it has more text
                if len(description) > len(text):
                    text = description

                # Extract date
                date_match = re.search(r"<pubDate>(.*?)</pubDate>", item)
                created_at = None
                if date_match:
                    try:
                        created_at = datetime.strptime(
                            date_match.group(1).strip(),
                            "%a, %d %b %Y %H:%M:%S %Z",
                        )
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        pass

                # Extract URLs from text
                urls = re.findall(r"https?://[^\s<]+", text)

                # Extract hashtags
                hashtags = re.findall(r"#(\w+)", text)

                # Extract mentions
                mentions = re.findall(r"@(\w+)", text)

                # Fix tweet URL (Nitter URL → X URL)
                if tweet_url and "nitter" in tweet_url:
                    tweet_url = re.sub(
                        r"https?://[^/]+/", "https://x.com/", tweet_url, count=1
                    )

                posts.append(Post(
                    tweet_id=tweet_id,
                    author_username=author_username,
                    author_display_name=None,
                    text=text,
                    tweet_url=tweet_url,
                    created_at=created_at,
                    urls=urls,
                    hashtags=hashtags,
                    mentions=mentions,
                ))

            except Exception as e:
                self.logger.debug(f"Error parsing RSS item: {e}")
                continue

        return posts

    def _clean_xml(self, text: str) -> str:
        """Clean XML entities and CDATA."""
        text = re.sub(r"<!\[CDATA\[", "", text)
        text = re.sub(r"\]\]>", "", text)
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        return text.strip()
