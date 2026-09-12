"""Main monitoring service — orchestrates all components."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from config import Config
from database.db import Database
from models.post import Post
from parser.post_parser import PostParser
from scoring.scorer import Scorer
from services.dedup import Deduplicator
from x_provider.provider import XProvider
from x_provider.playwright_provider import PlaywrightXProvider
from notifier.telegram import TelegramNotifier


class Monitor:
    """Main monitoring loop — connects all components."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self._running = False

        # Components (initialized in run)
        self.db: Database | None = None
        self.provider: XProvider | None = None
        self.parser = PostParser()
        self.scorer = Scorer(config, logger)
        self.dedup: Deduplicator | None = None
        self.notifier: TelegramNotifier | None = None

    async def _initialize(self) -> None:
        """Initialize all components."""
        self.logger.info("Initializing Arc NFT Whitelist Hunter...")

        # Database
        self.db = Database(self.config, self.logger)
        await self.db.initialize()

        # Deduplicator
        self.dedup = Deduplicator(self.db, self.logger)

        # Telegram
        self.notifier = TelegramNotifier(self.config, self.logger)
        if self.config.telegram_configured():
            self.logger.info("Telegram notifications: ENABLED")
        else:
            self.logger.info("Telegram notifications: DISABLED (not configured)")

        # Discord
        from notifier.discord import DiscordNotifier
        self.discord = DiscordNotifier(self.config, self.logger)
        if self.discord.is_configured():
            self.logger.info("Discord notifications: ENABLED")
        else:
            self.logger.info("Discord notifications: DISABLED (not configured)")

        # X Provider — use HTTP for cloud (no browser), Playwright for local
        use_http = os.getenv("USE_HTTP_PROVIDER", "").lower() in ("1", "true", "yes")

        if use_http:
            self.logger.info("Using HTTP X provider (no browser)")
            from x_provider.http_provider import HttpXProvider
            self.provider = HttpXProvider(self.config, self.logger)
        else:
            self.logger.info("Using Playwright X provider (browser)")
            self.provider = PlaywrightXProvider(self.config, self.logger)
        await self.provider.initialize()

        # Validate X session
        is_auth = await self.provider.validate_session()
        if not is_auth:
            if self.config.x_cookies_configured():
                self.logger.error("X session not authenticated — cookies may be expired.")
                self.logger.error("Please refresh X_AUTH_TOKEN and X_CT0 in .env.")
                self.logger.error("Run: python app.py --login")
            else:
                self.logger.error("X session not authenticated!")
                self.logger.error("Please run: python app.py --login")
            raise RuntimeError("X session not authenticated")

        self.logger.info("All components initialized successfully.")

    async def _cleanup(self) -> None:
        """Cleanup all components."""
        if self.provider:
            await self.provider.close()
        if self.db:
            await self.db.close()
        self.logger.info("Cleanup complete.")

    async def run_once(self) -> None:
        """Run one monitoring cycle."""
        try:
            await self._initialize()
            await self._execute_cycle()
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
        finally:
            await self._cleanup()

    async def run_continuous(self) -> None:
        """Run continuous monitoring loop."""
        try:
            await self._initialize()
            self._running = True

            self.logger.info(
                f"Starting continuous monitoring "
                f"(interval: {self.config.poll_interval_seconds}s)"
            )

            while self._running:
                try:
                    await self._execute_cycle()
                except Exception as e:
                    self.logger.error(f"Error in cycle: {e}", exc_info=True)

                if self._running:
                    self.logger.info(
                        f"Sleeping {self.config.poll_interval_seconds}s "
                        f"until next cycle..."
                    )
                    await asyncio.sleep(self.config.poll_interval_seconds)

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user.")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            self._running = False
            await self._cleanup()

    async def _execute_cycle(self) -> None:
        """Execute one full monitoring cycle."""
        self.logger.info("=" * 50)
        self.logger.info("MONITORING CYCLE START")
        self.logger.info("=" * 50)

        total_collected = 0
        total_new = 0
        total_relevant = 0
        total_high = 0
        total_medium = 0
        total_notified = 0

        for query in self.config.search_queries:
            if not self._running and hasattr(self, '_once_mode'):
                break

            self.logger.info(f"Query: {query}")

            try:
                # Search
                posts = await self.provider.search_posts(
                    query,
                    max_results=self.config.max_posts_per_query,
                )
                total_collected += len(posts)

                # Deduplicate
                new_posts = await self.dedup.filter_new(posts)
                total_new += len(new_posts)

                self.logger.info(
                    f"  Collected: {len(posts)}, New: {len(new_posts)}"
                )

                # Log search
                await self.db.log_search(query, len(posts), len(new_posts))

                # Process each new post
                for post in new_posts:
                    scored = self._process_post(post)
                    if scored and scored.priority != "IGNORE":
                        total_relevant += 1
                        if scored.priority == "HIGH":
                            total_high += 1
                        elif scored.priority == "MEDIUM":
                            total_medium += 1

                        # Store in DB
                        await self._store_post(scored)

                        # Send Telegram notification
                        if self.notifier:
                            sent = await self.notifier.send_alert(scored)
                            if sent:
                                total_notified += 1
                                await self.db.mark_notified(post.tweet_id)

                        # Send Discord notification
                        if self.discord:
                            await self.discord.send_alert(scored)

                # Delay between queries
                await asyncio.sleep(self.config.search_delay_seconds)

            except Exception as e:
                self.logger.error(f"Error processing query '{query}': {e}")
                continue

        # Summary
        self.logger.info("-" * 50)
        self.logger.info("CYCLE SUMMARY")
        self.logger.info(f"  Posts collected: {total_collected}")
        self.logger.info(f"  New posts: {total_new}")
        self.logger.info(f"  Relevant: {total_relevant}")
        self.logger.info(f"  HIGH priority: {total_high}")
        self.logger.info(f"  MEDIUM priority: {total_medium}")
        self.logger.info(f"  Telegram notifications sent: {total_notified}")
        self.logger.info("=" * 50)

    def _process_post(self, post: Post):
        """Parse and score a post."""
        try:
            scored = self.parser.parse(post)
            scored = self.scorer.score(scored)
            return scored
        except Exception as e:
            self.logger.error(f"Error processing post {post.tweet_id}: {e}")
            return None

    async def _store_post(self, scored) -> None:
        """Store a scored post in the database."""
        try:
            await self.db.insert_post(
                tweet_id=scored.post.tweet_id,
                author_username=scored.post.author_username,
                author_display_name=scored.post.author_display_name,
                text=scored.post.text,
                tweet_url=scored.post.tweet_url,
                created_at=(
                    scored.post.created_at.isoformat()
                    if scored.post.created_at
                    else None
                ),
                project_name=scored.project_name,
                project_username=scored.project_username,
                relevance_score=scored.score,
                priority=scored.priority,
                whitelist_url=scored.whitelist_url,
                mint_url=scored.mint_url,
                website_url=scored.website_url,
                discord_url=scored.discord_url,
                mint_date=scored.mint_date,
                whitelist_deadline=scored.whitelist_deadline,
                supply=scored.supply,
                whitelist_type=scored.whitelist_type,
            )

            # Also upsert project
            if scored.project_name or scored.project_username:
                await self.db.upsert_project(
                    name=scored.project_name,
                    x_username=scored.project_username,
                    website=scored.website_url,
                )

        except Exception as e:
            self.logger.error(f"Error storing post {scored.post.tweet_id}: {e}")

    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False
