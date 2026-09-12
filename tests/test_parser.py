"""Test post parser — keyword detection, URL extraction, project detection."""
from __future__ import annotations

import pytest
from models.post import Post
from parser.post_parser import (
    PostParser,
    detect_arc_relevance,
    detect_nft_relevance,
    detect_whitelist_relevance,
    extract_metadata,
)
from parser.url_parser import extract_urls, classify_url, extract_and_classify_urls
from parser.project_detector import detect_project_name, detect_project_username


class TestArcRelevance:
    """Test Arc Network relevance detection."""

    def test_arc_network_mentioned(self):
        assert detect_arc_relevance("Whitelist open for Arc Network NFT collection") is True

    def test_arc_dot_network(self):
        assert detect_arc_relevance("Check out arc.network for details") is True

    def test_at_arc_mention(self):
        assert detect_arc_relevance("@arc is launching something big") is True

    def test_no_arc(self):
        assert detect_arc_relevance("Bitcoin whitelist is open") is False

    def test_arc_blockchain_context(self):
        assert detect_arc_relevance("Arc blockchain has great tech") is True


class TestNftRelevance:
    """Test NFT relevance detection."""

    def test_nft_mentioned(self):
        assert detect_nft_relevance("NFT collection launching soon") is True

    def test_mint_mentioned(self):
        assert detect_nft_relevance("Public mint starts tomorrow") is True

    def test_drop_mentioned(self):
        assert detect_nft_relevance("NFT drop is live") is True

    def test_collection_mentioned(self):
        assert detect_nft_relevance("New collection revealed") is True

    def test_no_nft(self):
        assert detect_nft_relevance("Token price is pumping") is False


class TestWhitelistRelevance:
    """Test whitelist relevance detection."""

    def test_whitelist_mentioned(self):
        assert detect_whitelist_relevance("Whitelist is now open") is True

    def test_wl_mentioned(self):
        assert detect_whitelist_relevance("WL spots available") is True

    def test_allowlist_mentioned(self):
        assert detect_whitelist_relevance("Allowlist registration open") is True

    def test_gtd_mentioned(self):
        assert detect_whitelist_relevance("GTD spots for early supporters") is True

    def test_fcfs_mentioned(self):
        assert detect_whitelist_relevance("FCFS mint next week") is True

    def test_apply_mentioned(self):
        assert detect_whitelist_relevance("Apply for whitelist now") is True

    def test_no_whitelist(self):
        assert detect_whitelist_relevance("Just a regular post about crypto") is False


class TestUrlExtraction:
    """Test URL extraction and classification."""

    def test_extract_urls_from_text(self):
        urls = extract_urls("Check https://example.com/whitelist for details", [])
        assert "https://example.com/whitelist" in urls

    def test_extract_urls_from_post_urls(self):
        urls = extract_urls("", ["https://discord.gg/test"])
        assert "https://discord.gg/test" in urls

    def test_classify_whitelist_url(self):
        assert classify_url("https://example.com/whitelist") == "WHITELIST"

    def test_classify_mint_url(self):
        assert classify_url("https://example.com/mint") == "MINT"

    def test_classify_discord_url(self):
        assert classify_url("https://discord.gg/arcpunks") == "DISCORD"

    def test_classify_x_url(self):
        assert classify_url("https://x.com/user/status/123") == "X"

    def test_classify_website_url(self):
        assert classify_url("https://arcpunks.io") == "WEBSITE"

    def test_classify_unknown_url(self):
        assert classify_url("https://random-site.xyz") == "WEBSITE"


class TestPostParser:
    """Test full post parsing."""

    def setup_method(self):
        self.parser = PostParser()

    def test_full_parse_arc_nft_wl(self):
        post = Post(
            tweet_id="1",
            author_username="test",
            text="Whitelist open for Arc Network NFT collection at https://example.com/whitelist",
            tweet_url="https://x.com/test/status/1",
            urls=["https://example.com/whitelist"],
        )
        scored = self.parser.parse(post)
        assert scored.is_arc_relevant is True
        assert scored.is_nft_relevant is True
        assert scored.is_whitelist_relevant is True
        assert scored.whitelist_url == "https://example.com/whitelist"

    def test_parse_no_arc(self):
        post = Post(
            tweet_id="2",
            author_username="test",
            text="Bitcoin price is going up!",
            tweet_url="https://x.com/test/status/2",
        )
        scored = self.parser.parse(post)
        assert scored.is_arc_relevant is False

    def test_parse_metadata_extraction(self):
        post = Post(
            tweet_id="3",
            author_username="test",
            text="GTD whitelist open! Supply: 10000 NFTs. Mint on 15 October 2026.",
            tweet_url="https://x.com/test/status/3",
        )
        scored = self.parser.parse(post)
        assert scored.whitelist_type == "GTD"
        assert scored.supply == "10000"
        assert scored.mint_date is not None


class TestProjectDetection:
    """Test project name/username detection."""

    def test_detect_username(self):
        post = Post(tweet_id="1", author_username="arc_punks", text="test")
        assert detect_project_username(post) == "arc_punks"

    def test_detect_username_none(self):
        post = Post(tweet_id="1", author_username="", text="test")
        assert detect_project_username(post) is None
