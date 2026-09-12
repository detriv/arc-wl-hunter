"""Test scoring engine."""
from __future__ import annotations

import pytest
from config import Config
from models.post import Post, ScoredPost
from parser.post_parser import PostParser
from scoring.scorer import Scorer


class TestScoring:
    """Test relevance scoring."""

    def setup_method(self):
        self.config = Config.load()
        self.scorer = Scorer(self.config)
        self.parser = PostParser()

    def _score_post(self, text: str, urls: list[str] | None = None) -> ScoredPost:
        post = Post(
            tweet_id="test",
            author_username="test_user",
            text=text,
            tweet_url="https://x.com/test_user/status/1",
            urls=urls or [],
        )
        scored = self.parser.parse(post)
        return self.scorer.score(scored)

    def test_high_score_arc_nft_wl_url(self):
        """Arc + NFT + Whitelist + URL = HIGH."""
        scored = self._score_post(
            "Whitelist is now open for our NFT collection launching on Arc Network! Apply at https://example.com/whitelist",
            ["https://example.com/whitelist"],
        )
        assert scored.score >= 80
        assert scored.priority == "HIGH"

    def test_medium_score_arc_nft(self):
        """Arc + NFT without strong WL signals = MEDIUM."""
        scored = self._score_post(
            "New NFT collection coming to Arc Network soon. Stay tuned for details.",
        )
        assert 60 <= scored.score < 80
        assert scored.priority == "MEDIUM"

    def test_ignore_arc_only(self):
        """Arc only (no NFT/WL) = IGNORE."""
        scored = self._score_post(
            "Arc Network has impressive TPS. The technology is solid.",
        )
        assert scored.score < 60
        assert scored.priority == "IGNORE"

    def test_ignore_trading_talk(self):
        """Trading discussion = IGNORE."""
        scored = self._score_post(
            "Check this token price chart! Trading volume is pumping. Buy now!",
        )
        assert scored.priority == "IGNORE"

    def test_gtd_bonus(self):
        """GTD allocation adds bonus points."""
        scored = self._score_post(
            "GTD spots available for Arc NFT whitelist. Apply now!",
        )
        assert scored.score >= 60

    def test_fcfs_bonus(self):
        """FCFS allocation adds bonus points."""
        scored = self._score_post(
            "FCFS mint open for Arc Network NFT collection!",
        )
        assert scored.score >= 60

    def test_discord_url_bonus(self):
        """Discord URL adds small bonus."""
        scored = self._score_post(
            "Arc Network NFT whitelist open! Join our Discord: https://discord.gg/arcpunks",
            ["https://discord.gg/arcpunks"],
        )
        assert scored.score >= 60

    def test_score_clamped_to_100(self):
        """Score should never exceed 100."""
        scored = self._score_post(
            "Arc Network NFT whitelist GTD FCFS mint drop collection! "
            "Apply at https://example.com/whitelist. "
            "Discord: https://discord.gg/test. "
            "Website: https://test.com",
            ["https://example.com/whitelist", "https://discord.gg/test", "https://test.com"],
        )
        assert scored.score <= 100

    def test_score_never_negative(self):
        """Score should never be negative."""
        scored = self._score_post(
            "Random post about nothing relevant at all.",
        )
        assert scored.score >= 0

    def test_arc_alone_not_sufficient(self):
        """Arc keyword alone should not produce HIGH score."""
        scored = self._score_post(
            "Arc blockchain technology is improving.",
        )
        assert scored.priority == "IGNORE"

    def test_arc_nft_wl_very_strong(self):
        """Arc + NFT + WL + URL = very strong HIGH."""
        scored = self._score_post(
            "Whitelist officially open! Genesis NFT collection on Arc Network. "
            "GTD guaranteed spots. Apply: https://arcpunks.io/whitelist",
            ["https://arcpunks.io/whitelist"],
        )
        assert scored.score >= 90
        assert scored.priority == "HIGH"
