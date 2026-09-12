"""Test Telegram message formatting."""
from __future__ import annotations

import pytest
from models.post import Post, ScoredPost
from notifier.formatter import format_high_alert, format_medium_alert, format_test_message
from datetime import datetime, timezone


class TestFormatter:
    """Test Telegram message formatting."""

    def test_high_alert_contains_key_info(self):
        post = ScoredPost(
            post=Post(
                tweet_id="123",
                author_username="arc_punks",
                author_display_name="Arc Punks",
                text="Whitelist is officially open for our NFT collection launching on Arc Network!",
                tweet_url="https://x.com/arc_punks/status/123",
                created_at=datetime(2026, 9, 12, 6, 35, tzinfo=timezone.utc),
                urls=["https://arcpunks.io/whitelist"],
            ),
            score=92,
            priority="HIGH",
            is_arc_relevant=True,
            is_nft_relevant=True,
            is_whitelist_relevant=True,
            project_name="Arc Punks",
            project_username="arc_punks",
            whitelist_url="https://arcpunks.io/whitelist",
            discord_url="https://discord.gg/arcpunks",
            website_url="https://arcpunks.io",
            whitelist_type="GTD",
            supply="5000",
        )
        msg = format_high_alert(post)

        assert "ARC NFT WHITELIST DETECTED" in msg
        assert "@arc_punks" in msg
        assert "92" in msg
        assert "GTD" in msg
        assert "5000" in msg
        assert '<a href="https://arcpunks.io/whitelist">' in msg
        assert '<a href="https://discord.gg/arcpunks">' in msg

    def test_medium_alert_contains_key_info(self):
        post = ScoredPost(
            post=Post(
                tweet_id="456",
                author_username="nft_example",
                author_display_name="Example NFT",
                text="NFT project coming soon on Arc.",
                tweet_url="https://x.com/nft_example/status/456",
                created_at=datetime(2026, 9, 12, 8, 0, tzinfo=timezone.utc),
            ),
            score=67,
            priority="MEDIUM",
            is_arc_relevant=True,
            is_nft_relevant=True,
            is_whitelist_relevant=True,
            project_name="Example NFT",
        )
        msg = format_medium_alert(post)

        assert "ARC NFT OPPORTUNITY" in msg
        assert "@nft_example" in msg
        assert "67" in msg

    def test_test_message(self):
        msg = format_test_message()
        assert "Arc NFT Whitelist Hunter" in msg
        assert "Telegram connection is working" in msg

    def test_html_escaping(self):
        """Test that HTML special characters are escaped."""
        post = ScoredPost(
            post=Post(
                tweet_id="789",
                author_username="test",
                text="Price < $100 & supply > 500",
                tweet_url="https://x.com/test/status/789",
            ),
            score=50,
            priority="MEDIUM",
        )
        msg = format_medium_alert(post)

        assert "&lt; $100 &amp; supply &gt; 500" in msg
        assert "<script>" not in msg

    def test_url_in_html_link(self):
        """Test URLs are properly formatted as HTML links."""
        post = ScoredPost(
            post=Post(
                tweet_id="100",
                author_username="test",
                text="Whitelist open!",
                tweet_url="https://x.com/test/status/100",
            ),
            score=80,
            priority="HIGH",
            whitelist_url="https://example.com/whitelist",
        )
        msg = format_high_alert(post)

        # URL should be in an <a> tag, not escaped
        assert '<a href="https://example.com/whitelist">' in msg
        assert "https://example.com/whitelist</a>" in msg

    def test_no_markdown_v2_escape_artifacts(self):
        """Ensure no MarkdownV2 backslash escapes in HTML mode."""
        post = ScoredPost(
            post=Post(
                tweet_id="200",
                author_username="test",
                text="Check example.com for details. Apply now!",
                tweet_url="https://x.com/test/status/200",
            ),
            score=70,
            priority="HIGH",
            whitelist_url="https://example.com/apply",
        )
        msg = format_high_alert(post)

        # In HTML mode, dots should NOT be escaped
        assert "example.com for details" in msg
        assert "\\." not in msg
