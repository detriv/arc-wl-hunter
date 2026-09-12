"""Telegram notifier — sends alerts via Telegram Bot API."""
from __future__ import annotations

import logging

from telegram import Bot
from telegram.constants import ParseMode

from config import Config
from models.post import ScoredPost
from notifier.formatter import (
    format_high_alert,
    format_medium_alert,
    format_test_message,
)


class TelegramNotifier:
    """Sends notifications to Telegram."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self._bot: Bot | None = None

        if config.telegram_configured():
            self._bot = Bot(token=config.telegram_bot_token)

    async def send_test_message(self) -> bool:
        """Send a test message to verify Telegram configuration."""
        if not self._bot:
            self.logger.error("Telegram bot not initialized. Check .env configuration.")
            return False

        try:
            await self._bot.send_message(
                chat_id=self.config.telegram_chat_id,
                text=format_test_message(),
                parse_mode=ParseMode.HTML,
            )
            return True
        except Exception as e:
            self.logger.error(f"Telegram test failed: {e}")
            return False

    async def send_alert(self, post: ScoredPost) -> bool:
        """Send an alert for a scored post."""
        if not self._bot:
            self.logger.debug("Telegram not configured, skipping notification.")
            return False

        if post.priority == "HIGH":
            message = format_high_alert(post)
        elif post.priority == "MEDIUM":
            message = format_medium_alert(post)
        else:
            return False  # Don't send IGNORE

        try:
            # Telegram message limit is 4096 chars
            if len(message) > 4096:
                message = message[:4093] + "..."

            await self._bot.send_message(
                chat_id=self.config.telegram_chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
            self.logger.info(
                f"Telegram alert sent: @{post.post.author_username} "
                f"(score={post.score}, {post.priority})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
            return False
