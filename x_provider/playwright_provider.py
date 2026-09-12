"""Playwright-based X/Twitter provider using persistent browser context."""
from __future__ import annotations

import asyncio
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import (
    async_playwright,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeout,
)

from config import Config
from models.post import Post
from x_provider.provider import XProvider
from x_provider.selectors import (
    ARTICLE_SELECTOR,
    TEXT_SELECTOR,
    USER_NAME_SELECTOR,
    USERNAME_LINK_SELECTOR,
    TWEET_LINK_SELECTOR,
    LOGIN_AVATAR_SELECTOR,
    LOGIN_HEADER_SELECTOR,
    TIMELINE_SELECTOR,
)


class PlaywrightXProvider(XProvider):
    """X provider using Playwright + Chromium persistent context."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        super().__init__(config, logger)
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def initialize(self) -> None:
        """Launch Chromium with persistent context."""
        self.logger.info("Launching Chromium...")

        profile_dir = Path(self.config.browser_profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=self.config.browser_headless,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Use the first page or create one
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        # Inject X session cookies if configured
        if self.config.x_cookies_configured():
            await self._inject_x_cookies()

        self.logger.info("Chromium launched successfully.")

    async def _inject_x_cookies(self) -> None:
        """Inject X session cookies from .env into the browser context."""
        self.logger.info("Injecting X session cookies...")
        cookies = [
            {
                "name": "auth_token",
                "value": self.config.x_auth_token,
                "domain": ".x.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
            },
            {
                "name": "ct0",
                "value": self.config.x_ct0,
                "domain": ".x.com",
                "path": "/",
                "secure": True,
            },
        ]
        await self._context.add_cookies(cookies)
        self.logger.info("X session cookies injected.")

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._page = None
        self.logger.info("Browser closed.")

    async def _ensure_page(self) -> Page:
        """Ensure we have a valid page."""
        if not self._page or self._page.is_closed():
            if self._context:
                self._page = await self._context.new_page()
            else:
                raise RuntimeError("Browser context not available")
        return self._page

    async def validate_session(self) -> bool:
        """Check if X session is authenticated."""
        try:
            page = await self._ensure_page()
            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # Check for login indicators
            avatar = await page.query_selector(LOGIN_AVATAR_SELECTOR)
            home_link = await page.query_selector(LOGIN_HEADER_SELECTOR)

            if avatar or home_link:
                # Try to get username
                username = await self._extract_username(page)
                if username:
                    self.logger.info(f"X session authenticated: @{username}")
                else:
                    self.logger.info("X session authenticated.")
                return True

            # Check if we're on login page
            url = page.url
            if "login" in url or "flow" in url or "i/flow" in url:
                self.logger.warning("X session NOT authenticated (on login page).")
                return False

            # Additional check: look for common auth elements
            sign_in_btn = await page.query_selector('a[href="/login"]')
            if sign_in_btn:
                self.logger.warning("X session NOT authenticated (login button found).")
                return False

            self.logger.warning("X session status uncertain, assuming not authenticated.")
            return False

        except PlaywrightTimeout:
            self.logger.error("Timeout validating X session.")
            return False
        except Exception as e:
            self.logger.error(f"Error validating X session: {e}")
            return False

    async def _extract_username(self, page: Page) -> str | None:
        """Extract the current user's username."""
        try:
            avatar = await page.query_selector(LOGIN_AVATAR_SELECTOR)
            if avatar:
                aria_label = await avatar.get_attribute("aria-label")
                if aria_label:
                    # Format is typically "Profile @username"
                    match = re.search(r"@(\w+)", aria_label)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return None

    async def login_flow(self) -> None:
        """Launch browser for manual X login."""
        self.logger.info("Starting Chromium for X login...")

        profile_dir = Path(self.config.browser_profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,  # Must be visible for manual login
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        page = self._page
        await page.goto("https://x.com/login", wait_until="domcontentloaded", timeout=30000)

        print("\n" + "=" * 50)
        print("Please log into your X account manually.")
        print("Complete any verification steps if required.")
        print()
        input("Press ENTER after login is complete...")
        print("=" * 50 + "\n")

        # Validate
        await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        is_auth = await self.validate_session()
        if is_auth:
            print("\n✓ X authentication detected.")
            print(f"✓ Persistent browser profile saved to: {self.config.browser_profile_dir}")
            print("\nYou can now run: python app.py")
        else:
            print("\n✗ Could not verify X authentication.")
            print("Please try again: python app.py --login")

        await self.close()

    async def search_posts(
        self,
        query: str,
        max_results: int | None = None,
    ) -> list[Post]:
        """Search X for posts matching the query with scrolling."""
        max_results = max_results or self.config.max_posts_per_query
        max_scrolls = self.config.max_scrolls_per_query
        scroll_delay = self.config.scroll_delay_seconds

        posts: list[Post] = []
        seen_ids: set[str] = set()

        try:
            page = await self._ensure_page()

            # Navigate to search
            encoded_query = quote(query)
            search_url = f"https://x.com/search?q={encoded_query}&f=live"
            self.logger.info(f"Searching: {query}")

            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            # Wait for timeline to load
            try:
                await page.wait_for_selector(ARTICLE_SELECTOR, timeout=15000)
            except PlaywrightTimeout:
                self.logger.warning(f"No posts found for query: {query}")
                return posts

            scroll_count = 0
            no_new_count = 0

            while len(posts) < max_results and scroll_count < max_scrolls:
                # Extract visible posts
                new_posts = await self._extract_posts(page, seen_ids)
                posts.extend(new_posts)

                if not new_posts:
                    no_new_count += 1
                    if no_new_count >= 2:
                        break
                else:
                    no_new_count = 0

                if len(posts) >= max_results:
                    break

                # Scroll down
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(scroll_delay)
                scroll_count += 1

            self.logger.info(
                f"Query '{query}': collected {len(posts)} posts "
                f"({scroll_count} scrolls)"
            )

        except PlaywrightTimeout:
            self.logger.warning(f"Timeout searching for: {query}")
        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {e}")

        return posts[:max_results]

    async def _extract_posts(self, page: Page, seen_ids: set[str]) -> list[Post]:
        """Extract posts from the current page state."""
        posts = []

        try:
            articles = await page.query_selector_all(ARTICLE_SELECTOR)

            for article in articles:
                try:
                    post = await self._parse_article(article)
                    if post and post.tweet_id and post.tweet_id not in seen_ids:
                        seen_ids.add(post.tweet_id)
                        posts.append(post)
                except Exception as e:
                    self.logger.debug(f"Error parsing article: {e}")
                    continue

        except Exception as e:
            self.logger.debug(f"Error extracting posts: {e}")

        return posts

    async def _parse_article(self, article) -> Post | None:
        """Parse a single article element into a Post."""
        try:
            # Extract tweet ID from link
            tweet_id = ""
            tweet_url = ""

            link_els = await article.query_selector_all(TWEET_LINK_SELECTOR)
            for link_el in link_els:
                href = await link_el.get_attribute("href")
                if href and "/status/" in href:
                    # Extract tweet ID
                    match = re.search(r"/status/(\d+)", href)
                    if match:
                        tweet_id = match.group(1)
                        tweet_url = f"https://x.com{href}" if href.startswith("https") else f"https://x.com{href}"
                        break

            if not tweet_id:
                return None

            # Extract text
            text = ""
            text_el = await article.query_selector(TEXT_SELECTOR)
            if text_el:
                text = await text_el.inner_text()

            if not text:
                return None

            # Extract author info
            author_username = ""
            author_display_name = None

            user_el = await article.query_selector(USER_NAME_SELECTOR)
            if user_el:
                # Get all links within user element
                user_links = await user_el.query_selector_all("a[role='link']")
                for link in user_links:
                    href = await link.get_attribute("href")
                    if href and href.startswith("/"):
                        author_username = href.strip("/").split("/")[0]
                        # Get display name from the text content
                        name_span = await link.query_selector("span")
                        if name_span:
                            display = await name_span.inner_text()
                            if display and display != author_username:
                                author_display_name = display
                        break

            # Extract timestamp
            created_at = None
            time_el = await article.query_selector("time")
            if time_el:
                datetime_str = await time_el.get_attribute("datetime")
                if datetime_str:
                    try:
                        created_at = datetime.fromisoformat(
                            datetime_str.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass

            # Extract URLs from text
            urls = re.findall(r"https?://[^\s]+", text)

            # Extract hashtags
            hashtags = re.findall(r"#(\w+)", text)

            # Extract mentions
            mentions = re.findall(r"@(\w+)", text)

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
            self.logger.debug(f"Parse article error: {e}")
            return None
