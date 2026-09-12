"""Relevance scoring engine."""
from __future__ import annotations

import logging

from config import Config
from models.post import ScoredPost
from scoring.keywords import (
    ARC_KEYWORDS,
    NFT_KEYWORDS,
    WHITELIST_KEYWORDS,
    ALLOCATION_KEYWORDS,
    APPLICATION_KEYWORDS,
    NEGATIVE_KEYWORDS,
)


# ── Scoring weights ─────────────────────────────────
POSITIVE_WEIGHTS = {
    "arc_explicit": 30,        # Arc Network explicitly mentioned
    "arc_nft_project": 25,     # Arc NFT project identified
    "nft_keyword": 15,         # NFT keyword present
    "whitelist_keyword": 30,   # Whitelist keyword present
    "allowlist_keyword": 30,   # Allowlist keyword present
    "mint_keyword": 10,        # Mint keyword present
    "gtd": 10,                 # GTD allocation
    "fcfs": 10,                # FCFS allocation
    "whitelist_url": 15,       # Whitelist URL found
    "mint_url": 10,            # Mint URL found
    "application_url": 10,     # Application URL found
    "discord_url": 5,          # Discord URL found
    "project_mentioned": 5,    # Project X account mentioned
}

NEGATIVE_WEIGHTS = {
    "generic_crypto": -10,          # Generic crypto discussion
    "giveaway_no_nft": -20,         # Giveaway without NFT/WL context
    "airdrop_no_nft": -20,          # Airdrop unrelated to NFT
    "token_price": -20,             # Token price discussion
    "trading": -20,                 # Trading discussion
    "generic_arc_blockchain": -10,  # Generic Arc blockchain discussion
}


class Scorer:
    """Calculates relevance scores for posts."""

    def __init__(self, config: Config, logger: logging.Logger | None = None) -> None:
        self.config = config
        self.logger = logger

    def score(self, post: ScoredPost) -> ScoredPost:
        """Calculate relevance score for a ScoredPost."""
        score = 0
        text_lower = post.post.text.lower()

        # ── Positive signals ──────────────────────────

        # Arc Network explicitly mentioned
        if post.is_arc_relevant:
            score += POSITIVE_WEIGHTS["arc_explicit"]

            # Arc + NFT project identified
            if post.is_nft_relevant and post.project_name:
                score += POSITIVE_WEIGHTS["arc_nft_project"]

        # NFT keyword
        if post.is_nft_relevant:
            score += POSITIVE_WEIGHTS["nft_keyword"]

        # Whitelist keyword
        if post.is_whitelist_relevant:
            # Check specific type
            if any(kw in text_lower for kw in ["whitelist", "whitelisted"]):
                score += POSITIVE_WEIGHTS["whitelist_keyword"]
            elif any(kw in text_lower for kw in ["allowlist", "allow list"]):
                score += POSITIVE_WEIGHTS["allowlist_keyword"]

        # Mint keyword
        if any(kw in text_lower for kw in ["mint", "minting", "drop"]):
            score += POSITIVE_WEIGHTS["mint_keyword"]

        # GTD
        if "gtd" in text_lower or "guaranteed" in text_lower:
            score += POSITIVE_WEIGHTS["gtd"]

        # FCFS
        if "fcfs" in text_lower:
            score += POSITIVE_WEIGHTS["fcfs"]

        # Whitelist URL
        if post.whitelist_url:
            score += POSITIVE_WEIGHTS["whitelist_url"]

        # Mint URL
        if post.mint_url:
            score += POSITIVE_WEIGHTS["mint_url"]

        # Application URL (could be whitelist form or similar)
        if post.whitelist_url or post.mint_url:
            score += POSITIVE_WEIGHTS["application_url"]

        # Discord URL
        if post.discord_url:
            score += POSITIVE_WEIGHTS["discord_url"]

        # Project mentioned
        if post.project_username:
            score += POSITIVE_WEIGHTS["project_mentioned"]

        # ── Negative signals ──────────────────────────

        # Generic Arc blockchain discussion (no NFT/WL context)
        if post.is_arc_relevant and not post.is_nft_relevant and not post.is_whitelist_relevant:
            score += NEGATIVE_WEIGHTS["generic_arc_blockchain"]

        # Token price discussion
        if any(kw in text_lower for kw in ["price", "chart", "market cap", "marketcap"]):
            score += NEGATIVE_WEIGHTS["token_price"]

        # Trading discussion
        if any(kw in text_lower for kw in ["trading", "buy", "sell", "pump", "dump"]):
            score += NEGATIVE_WEIGHTS["trading"]

        # Giveaway without NFT/WL context
        if "giveaway" in text_lower and not post.is_nft_relevant:
            score += NEGATIVE_WEIGHTS["giveaway_no_nft"]

        # Airdrop unrelated to NFT
        if "airdrop" in text_lower and not post.is_nft_relevant:
            score += NEGATIVE_WEIGHTS["airdrop_no_nft"]

        # Generic crypto discussion (no Arc, no NFT)
        if not post.is_arc_relevant and not post.is_nft_relevant:
            if any(kw in text_lower for kw in NEGATIVE_KEYWORDS):
                score += NEGATIVE_WEIGHTS["generic_crypto"]

        # ── Clamp score ───────────────────────────────
        score = max(0, min(100, score))

        # ── Determine priority ────────────────────────
        if score >= self.config.high_priority_score:
            priority = "HIGH"
        elif score >= self.config.min_score:
            priority = "MEDIUM"
        else:
            priority = "IGNORE"

        post.score = score
        post.priority = priority

        return post
