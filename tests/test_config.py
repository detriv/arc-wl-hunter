"""Test configuration loading and validation."""
from __future__ import annotations

import os
import pytest
from config import Config


class TestConfig:
    """Test configuration module."""

    def test_default_config(self):
        """Test default configuration values."""
        # Clear env vars that might interfere
        env_backup = {}
        keys = [
            "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
            "BROWSER_PROFILE_DIR", "BROWSER_HEADLESS",
            "POLL_INTERVAL_SECONDS", "MIN_SCORE", "HIGH_PRIORITY_SCORE",
        ]
        for key in keys:
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)

        try:
            config = Config.load()
            assert config.telegram_bot_token is None
            assert config.telegram_chat_id is None
            assert config.browser_profile_dir == "data/browser-profile"
            assert config.browser_headless is False
            assert config.poll_interval_seconds == 300
            assert config.min_score == 60
            assert config.high_priority_score == 80
            assert len(config.search_queries) == 13
        finally:
            os.environ.update(env_backup)

    def test_config_validation_valid(self):
        """Test validation with valid config."""
        config = Config.load()
        errors = config.validate()
        assert len(errors) == 0

    def test_config_validation_invalid_scores(self):
        """Test validation catches invalid score thresholds."""
        config = Config(min_score=101, high_priority_score=80)
        errors = config.validate()
        assert any("MIN_SCORE" in e for e in errors)

    def test_config_validation_high_below_min(self):
        """Test validation catches HIGH < MIN."""
        config = Config(min_score=80, high_priority_score=60)
        errors = config.validate()
        assert any("HIGH_PRIORITY_SCORE" in e for e in errors)

    def test_config_validation_low_poll_interval(self):
        """Test validation catches too-low poll interval."""
        config = Config(poll_interval_seconds=30)
        errors = config.validate()
        assert any("POLL_INTERVAL_SECONDS" in e for e in errors)

    def test_telegram_configured(self):
        """Test telegram_configured check."""
        config = Config(telegram_bot_token="test", telegram_chat_id="123")
        assert config.telegram_configured() is True

        config2 = Config(telegram_bot_token=None, telegram_chat_id=None)
        assert config2.telegram_configured() is False

    def test_search_queries_present(self):
        """Test that default search queries include Arc-related terms."""
        config = Config.load()
        queries_str = " ".join(config.search_queries).lower()
        assert "arc" in queries_str
        assert "whitelist" in queries_str
        assert "nft" in queries_str
