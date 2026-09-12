"""Discord notifier — sends alerts via webhook."""
from __future__ import annotations

import logging

import httpx

from config import Config
from models.post import ScoredPost
from notifier.formatter import format_high_alert, format_medium_alert


class DiscordNotifier:
    """Sends notifications to Discord via webhook."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self._webhook_url = config.discord_webhook_url

    def is_configured(self) -> bool:
        return bool(self._webhook_url)

    async def send_alert(self, post: ScoredPost) -> bool:
        """Send an alert to Discord."""
        if not self._webhook_url:
            return False

        if post.priority == "HIGH":
            message = format_high_alert(post)
        elif post.priority == "MEDIUM":
            message = format_medium_alert(post)
        else:
            return False

        # Discord embed for richer formatting
        color = 0xFF4500 if post.priority == "HIGH" else 0xFFA500
        emoji = "🔥" if post.priority == "HIGH" else "🟡"
        title = f"{emoji} ARC NFT WHITELIST DETECTED" if post.priority == "HIGH" else f"{emoji} ARC NFT OPPORTUNITY"

        # Build fields
        fields = [
            {"name": "📌 Project", "value": post.project_name or post.project_username or "Unknown", "inline": True},
            {"name": "👤 Author", "value": f"@{post.post.author_username}", "inline": True},
            {"name": "📊 Score", "value": f"**{post.score}**", "inline": True},
        ]

        if post.whitelist_type:
            fields.append({"name": "🏷 Type", "value": post.whitelist_type, "inline": True})
        if post.supply:
            fields.append({"name": "📦 Supply", "value": post.supply, "inline": True})

        # URLs field
        urls_text = []
        if post.whitelist_url:
            urls_text.append(f"🎟 [Whitelist]({post.whitelist_url})")
        if post.mint_url:
            urls_text.append(f"⛏ [Mint]({post.mint_url})")
        if post.website_url:
            urls_text.append(f"🌐 [Website]({post.website_url})")
        if post.discord_url:
            urls_text.append(f"💬 [Discord]({post.discord_url})")
        if post.post.tweet_url:
            urls_text.append(f"🔗 [X Post]({post.post.tweet_url})")

        if urls_text:
            fields.append({"name": "🔗 Links", "value": " | ".join(urls_text), "inline": False})

        embed = {
            "title": title,
            "description": post.post.text[:300] + ("..." if len(post.post.text) > 300 else ""),
            "color": color,
            "fields": fields,
            "footer": {"text": f"Arc WL Hunter • Score: {post.score}"},
            "timestamp": post.post.created_at.isoformat() if post.post.created_at else None,
        }

        payload = {"embeds": [embed]}

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._webhook_url,
                    json=payload,
                    timeout=10,
                )
                resp.raise_for_status()
            self.logger.info(
                f"Discord alert sent: @{post.post.author_username} "
                f"(score={post.score}, {post.priority})"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to send Discord alert: {e}")
            return False

    async def send_test_message(self) -> bool:
        """Send a test message to Discord."""
        if not self._webhook_url:
            return False

        payload = {
            "embeds": [{
                "title": "✅ Arc NFT Whitelist Hunter",
                "description": "Discord webhook is configured correctly!\nYou will receive alerts here.",
                "color": 0x00FF00,
            }]
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._webhook_url,
                    json=payload,
                    timeout=10,
                )
                resp.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Discord test failed: {e}")
            return False
