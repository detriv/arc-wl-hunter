"""Arc NFT Whitelist Hunter — Main CLI entry point."""
from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from pathlib import Path

from config import Config, validate_required
from logger import setup_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="Arc NFT Whitelist Hunter — Monitor X for Arc NFT whitelist opportunities",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Launch browser for manual X login",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one monitoring cycle and exit",
    )
    parser.add_argument(
        "--test-x",
        action="store_true",
        help="Test X extraction (live)",
    )
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="Send test Telegram message",
    )
    parser.add_argument(
        "--test-discord",
        action="store_true",
        help="Send test Discord message",
    )
    parser.add_argument(
        "--test-db",
        action="store_true",
        help="Test database initialization",
    )
    parser.add_argument(
        "--test-parser",
        action="store_true",
        help="Test parser with sample data",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Run with FastAPI web server (for cloud deployment)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics",
    )
    return parser


async def run_login(config: Config, logger) -> None:
    """Show instructions for X login via cookies."""
    print()
    print("=" * 55)
    print("  X (Twitter) Authentication via Cookies")
    print("=" * 55)
    print()
    print("  X login via browser automation is often blocked.")
    print("  Instead, we use session cookies from your browser.")
    print()
    print("  Steps:")
    print()
    print("  1. Open https://x.com in Chrome/Firefox")
    print("  2. Login normally (if not already)")
    print("  3. Press F12 → Application → Cookies → https://x.com")
    print("  4. Find 'auth_token' → copy Value")
    print("  5. Find 'ct0' → copy Value")
    print("  6. Open .env and paste:")
    print()
    print("     X_AUTH_TOKEN=<auth_token value>")
    print("     X_CT0=<ct0 value>")
    print()
    print("  7. Run: python app.py --test-x")
    print()
    print("=" * 55)
    print()


async def run_monitor(config: Config, logger, once: bool = False) -> None:
    """Run the monitoring loop."""
    from services.monitor import Monitor

    monitor = Monitor(config, logger)
    if once:
        await monitor.run_once()
    else:
        await monitor.run_continuous()


async def run_test_x(config: Config, logger) -> None:
    """Test X extraction."""
    from x_provider.playwright_provider import PlaywrightXProvider

    logger.info("Testing X extraction...")
    provider = PlaywrightXProvider(config, logger)
    try:
        await provider.initialize()
        is_auth = await provider.validate_session()
        if not is_auth:
            logger.error("X session not authenticated. Run: python app.py --login")
            return

        query = '"Arc Network" NFT whitelist'
        logger.info(f"Searching: {query}")
        posts = await provider.search_posts(query, max_results=10)
        logger.info(f"Found {len(posts)} posts")

        for i, post in enumerate(posts, 1):
            logger.info(f"--- Post {i} ---")
            logger.info(f"Author: @{post.author_username}")
            logger.info(f"Text: {post.text[:150]}...")
            logger.info(f"URL: {post.tweet_url}")
            logger.info(f"Created: {post.created_at}")
            if post.urls:
                logger.info(f"URLs: {post.urls}")
            if post.hashtags:
                logger.info(f"Tags: {post.hashtags}")
            logger.info("")

        print(f"\n✓ Test complete. Found {len(posts)} posts.")
        print("  Press ENTER to close browser...")
        input()

    finally:
        await provider.close()


async def run_test_telegram(config: Config, logger) -> None:
    """Send test Telegram message."""
    if not config.telegram_configured():
        logger.error("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return

    from notifier.telegram import TelegramNotifier

    notifier = TelegramNotifier(config, logger)
    success = await notifier.send_test_message()
    if success:
        logger.info("Telegram test successful.")
    else:
        logger.error("Telegram test failed.")


async def run_test_discord(config: Config, logger) -> None:
    """Send test Discord message."""
    if not config.discord_webhook_url:
        logger.error("Discord not configured. Set DISCORD_WEBHOOK_URL in .env")
        return

    from notifier.discord import DiscordNotifier

    notifier = DiscordNotifier(config, logger)
    success = await notifier.send_test_message()
    if success:
        logger.info("Discord test successful.")
    else:
        logger.error("Discord test failed.")


async def run_test_db(config: Config, logger) -> None:
    """Test database initialization."""
    from database.db import Database

    db = Database(config, logger)
    await db.initialize()
    stats = await db.get_stats()
    logger.info("Database initialized successfully.")
    logger.info(f"Stats: {stats}")
    await db.close()


async def run_test_parser(config: Config, logger) -> None:
    """Test parser with sample data."""
    from models.post import Post
    from parser.post_parser import PostParser
    from scoring.scorer import Scorer

    parser = PostParser()
    scorer = Scorer(config)

    # Test cases
    test_posts = [
        Post(
            tweet_id="1",
            author_username="nft_project",
            author_display_name="NFT Project",
            text="Whitelist is now open for our NFT collection launching on Arc Network! Apply now at https://example.com/whitelist",
            tweet_url="https://x.com/nft_project/status/1",
            urls=["https://example.com/whitelist"],
        ),
        Post(
            tweet_id="2",
            author_username="crypto_trader",
            author_display_name="Crypto Trader",
            text="Arc Network has impressive TPS. The technology is solid.",
            tweet_url="https://x.com/crypto_trader/status/2",
        ),
        Post(
            tweet_id="3",
            author_username="arc_punks",
            author_display_name="Arc Punks",
            text="🎉 WL spots open! Our genesis NFT collection on Arc. GTD guaranteed for early supporters. Discord: https://discord.gg/arcpunks",
            tweet_url="https://x.com/arc_punks/status/3",
            urls=["https://discord.gg/arcpunks"],
        ),
    ]

    for post in test_posts:
        scored = parser.parse(post)
        scored = scorer.score(scored)
        logger.info(f"--- @{post.author_username} ---")
        logger.info(f"Text: {post.text[:80]}...")
        logger.info(f"Score: {scored.score} | Priority: {scored.priority}")
        logger.info(f"Arc: {scored.is_arc_relevant} | NFT: {scored.is_nft_relevant} | WL: {scored.is_whitelist_relevant}")
        if scored.whitelist_url:
            logger.info(f"WL URL: {scored.whitelist_url}")
        if scored.project_name:
            logger.info(f"Project: {scored.project_name}")


async def run_stats(config: Config, logger) -> None:
    """Show database statistics."""
    from database.db import Database

    db = Database(config, logger)
    await db.initialize()
    stats = await db.get_stats()
    await db.close()

    print("\nDATABASE STATISTICS")
    print("-------------------")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()


async def async_main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Load config
    config = Config.load()
    logger = setup_logging(config.log_level)

    # Validate config
    if not validate_required(config):
        sys.exit(1)

    # Print status
    config.print_status()
    print()

    # Route to appropriate handler
    try:
        if args.login:
            await run_login(config, logger)
        elif args.once:
            await run_monitor(config, logger, once=True)
        elif args.test_x:
            await run_test_x(config, logger)
        elif args.test_telegram:
            await run_test_telegram(config, logger)
        elif args.test_discord:
            await run_test_discord(config, logger)
        elif args.test_db:
            await run_test_db(config, logger)
        elif args.test_parser:
            await run_test_parser(config, logger)
        elif args.stats:
            await run_stats(config, logger)
        elif args.web:
            # Run with FastAPI web server (for cloud deployment)
            import uvicorn
            from main import app
            import os

            port = int(os.getenv("PORT", "8000"))
            uvicorn.run(app, host="0.0.0.0", port=port)
        else:
            # Default: continuous monitoring
            await run_monitor(config, logger, once=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
