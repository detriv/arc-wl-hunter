"""Test URL extraction and classification."""
from __future__ import annotations

import pytest
from parser.url_parser import extract_urls, classify_url, extract_and_classify_urls
from models.post import Post


class TestExtractUrls:
    """Test URL extraction from post text."""

    def test_single_url(self):
        urls = extract_urls("Visit https://example.com/page for info", [])
        assert "https://example.com/page" in urls

    def test_multiple_urls(self):
        urls = extract_urls(
            "WL: https://example.com/wl and Discord: https://discord.gg/test",
            [],
        )
        assert "https://example.com/wl" in urls
        assert "https://discord.gg/test" in urls

    def test_urls_from_post_metadata(self):
        urls = extract_urls("Check the link", ["https://example.com"])
        assert "https://example.com" in urls

    def test_no_urls(self):
        urls = extract_urls("No links here!", [])
        assert len(urls) == 0

    def test_url_with_trailing_punctuation(self):
        urls = extract_urls("Visit https://example.com.", [])
        assert "https://example.com" in urls


class TestClassifyUrl:
    """Test URL classification."""

    def test_whitelist_urls(self):
        assert classify_url("https://example.com/whitelist") == "WHITELIST"
        assert classify_url("https://example.com/wl-form") == "WHITELIST"

    def test_mint_urls(self):
        assert classify_url("https://example.com/mint") == "MINT"
        assert classify_url("https://example.com/mintnow") == "MINT"

    def test_discord_urls(self):
        assert classify_url("https://discord.gg/test") == "DISCORD"
        assert classify_url("https://discord.com/invite/test") == "DISCORD"

    def test_x_urls(self):
        assert classify_url("https://x.com/user") == "X"
        assert classify_url("https://twitter.com/user") == "X"

    def test_website_urls(self):
        assert classify_url("https://arcpunks.io") == "WEBSITE"
        assert classify_url("https://www.example.com") == "WEBSITE"


class TestExtractAndClassify:
    """Test combined extraction and classification."""

    def test_classified_urls(self):
        post = Post(
            tweet_id="1",
            author_username="test",
            text="WL: https://example.com/whitelist Discord: https://discord.gg/test",
            urls=["https://example.com/whitelist", "https://discord.gg/test"],
        )
        classified = extract_and_classify_urls(post)
        assert len(classified["WHITELIST"]) == 1
        assert len(classified["DISCORD"]) == 1
