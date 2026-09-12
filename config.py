"""Configuration module — loads and validates all settings from .env."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _getenv(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def _getenv_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"WARNING: {key} must be an integer, got '{raw}'. Using default {default}.")
        return default


def _getenv_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "yes")


@dataclass
class Config:
    """Centralized application configuration."""

    # Telegram
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    # X (Twitter) session cookies
    x_auth_token: str | None = None
    x_ct0: str | None = None

    # Browser
    browser_profile_dir: str = "data/browser-profile"
    browser_headless: bool = False

    # Monitoring
    poll_interval_seconds: int = 300

    # Search
    search_delay_seconds: int = 2
    scroll_delay_seconds: int = 2
    max_posts_per_query: int = 50
    max_scrolls_per_query: int = 10

    # Scoring
    min_score: int = 60
    high_priority_score: int = 80

    # Logging
    log_level: str = "INFO"

    # Search queries
    search_queries: list[str] = field(default_factory=lambda: [
        '"Arc Network" NFT whitelist',
        '"Arc Network" NFT WL',
        '"Arc Network" allowlist',
        '"Arc Network" NFT mint',
        '"Arc Network" whitelist mint',
        '"Arc" NFT whitelist',
        '"Arc" NFT WL',
        '"Arc" allowlist NFT',
        '"Arc" GTD NFT',
        '"Arc" FCFS NFT',
        '"Arc" whitelist application',
        '"Arc" NFT launch',
        '"Arc" NFT collection',
    ])

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            telegram_bot_token=_getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_getenv("TELEGRAM_CHAT_ID"),
            x_auth_token=_getenv("X_AUTH_TOKEN"),
            x_ct0=_getenv("X_CT0"),
            browser_profile_dir=_getenv("BROWSER_PROFILE_DIR", "data/browser-profile"),
            browser_headless=_getenv_bool("BROWSER_HEADLESS", False),
            poll_interval_seconds=_getenv_int("POLL_INTERVAL_SECONDS", 300),
            search_delay_seconds=_getenv_int("SEARCH_DELAY_SECONDS", 2),
            scroll_delay_seconds=_getenv_int("SCROLL_DELAY_SECONDS", 2),
            max_posts_per_query=_getenv_int("MAX_POSTS_PER_QUERY", 50),
            max_scrolls_per_query=_getenv_int("MAX_SCROLLS_PER_QUERY", 10),
            min_score=_getenv_int("MIN_SCORE", 60),
            high_priority_score=_getenv_int("HIGH_PRIORITY_SCORE", 80),
            log_level=_getenv("LOG_LEVEL", "INFO") or "INFO",
        )

    def validate(self) -> list[str]:
        """Validate configuration. Returns list of error messages."""
        errors = []

        if self.min_score < 0 or self.min_score > 100:
            errors.append(f"MIN_SCORE must be 0-100, got {self.min_score}")

        if self.high_priority_score < 0 or self.high_priority_score > 100:
            errors.append(f"HIGH_PRIORITY_SCORE must be 0-100, got {self.high_priority_score}")

        if self.high_priority_score < self.min_score:
            errors.append(
                f"HIGH_PRIORITY_SCORE ({self.high_priority_score}) "
                f"must be >= MIN_SCORE ({self.min_score})"
            )

        if self.poll_interval_seconds < 60:
            errors.append(
                f"POLL_INTERVAL_SECONDS must be >= 60, got {self.poll_interval_seconds}"
            )

        if self.max_posts_per_query < 1:
            errors.append(f"MAX_POSTS_PER_QUERY must be >= 1, got {self.max_posts_per_query}")

        if self.max_scrolls_per_query < 1:
            errors.append(f"MAX_SCROLLS_PER_QUERY must be >= 1, got {self.max_scrolls_per_query}")

        return errors

    def telegram_configured(self) -> bool:
        """Check if Telegram credentials are available."""
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    def x_cookies_configured(self) -> bool:
        """Check if X session cookies are available."""
        return bool(self.x_auth_token and self.x_ct0)

    def print_status(self) -> None:
        """Print configuration status (without secrets)."""
        token_status = "SET" if self.telegram_bot_token else "NOT SET"
        chat_status = "SET" if self.telegram_chat_id else "NOT SET"
        x_auth_status = "SET" if self.x_auth_token else "NOT SET"
        x_ct0_status = "SET" if self.x_ct0 else "NOT SET"

        print("CONFIGURATION STATUS")
        print("--------------------")
        print(f"TELEGRAM_BOT_TOKEN: {token_status}")
        print(f"TELEGRAM_CHAT_ID: {chat_status}")
        print(f"X_AUTH_TOKEN: {x_auth_status}")
        print(f"X_CT0: {x_ct0_status}")
        print(f"BROWSER_PROFILE_DIR: {self.browser_profile_dir}")
        print(f"BROWSER_HEADLESS: {self.browser_headless}")
        print(f"POLL_INTERVAL_SECONDS: {self.poll_interval_seconds}")
        print(f"SEARCH_DELAY_SECONDS: {self.search_delay_seconds}")
        print(f"SCROLL_DELAY_SECONDS: {self.scroll_delay_seconds}")
        print(f"MAX_POSTS_PER_QUERY: {self.max_posts_per_query}")
        print(f"MAX_SCROLLS_PER_QUERY: {self.max_scrolls_per_query}")
        print(f"MIN_SCORE: {self.min_score}")
        print(f"HIGH_PRIORITY_SCORE: {self.high_priority_score}")
        print(f"LOG_LEVEL: {self.log_level}")
        print(f"SEARCH_QUERIES: {len(self.search_queries)} queries")


def validate_required(config: Config) -> bool:
    """Validate and exit if required config is missing. Returns True if valid."""
    errors = config.validate()
    if errors:
        print("CONFIGURATION ERRORS:")
        for err in errors:
            print(f"  - {err}")
        return False
    return True
