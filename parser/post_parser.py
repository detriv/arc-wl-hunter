"""Post parser — detects Arc relevance, NFT relevance, whitelist opportunities."""
from __future__ import annotations

import re

from models.post import Post, ScoredPost
from parser.url_parser import extract_and_classify_urls, extract_project_website
from parser.project_detector import detect_project_name, detect_project_username
from scoring.keywords import (
    ARC_KEYWORDS,
    NFT_KEYWORDS,
    WHITELIST_KEYWORDS,
    ALLOCATION_KEYWORDS,
    APPLICATION_KEYWORDS,
)


def _contains_keyword(text: str, keywords: list[str]) -> bool:
    """Check if text contains any of the keywords (case-insensitive)."""
    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True
    return False


def detect_arc_relevance(text: str) -> bool:
    """Detect if the post is relevant to Arc Network."""
    return _contains_keyword(text, ARC_KEYWORDS)


def detect_nft_relevance(text: str) -> bool:
    """Detect if the post is NFT-related."""
    return _contains_keyword(text, NFT_KEYWORDS)


def detect_whitelist_relevance(text: str) -> bool:
    """Detect if the post mentions whitelist/allowlist opportunities."""
    has_wl = _contains_keyword(text, WHITELIST_KEYWORDS)
    has_allocation = _contains_keyword(text, ALLOCATION_KEYWORDS)
    has_application = _contains_keyword(text, APPLICATION_KEYWORDS)
    return has_wl or has_allocation or has_application


def extract_metadata(post: Post) -> dict:
    """Extract additional metadata from post text."""
    text = post.text
    metadata: dict = {}

    # Whitelist type detection
    text_lower = text.lower()
    if "gtd" in text_lower or "guaranteed" in text_lower:
        metadata["whitelist_type"] = "GTD"
    elif "fcfs" in text_lower:
        metadata["whitelist_type"] = "FCFS"
    elif "raffle" in text_lower or "lottery" in text_lower:
        metadata["whitelist_type"] = "Raffle"
    elif "application" in text_lower or "apply" in text_lower or "form" in text_lower:
        metadata["whitelist_type"] = "Application"

    # Supply detection
    supply_match = re.search(r"(\d[\d,]*)\s*(?:supply|items?|pieces?|nfts?|total)", text, re.IGNORECASE)
    if supply_match:
        metadata["supply"] = supply_match.group(1)

    # Date detection (simple patterns)
    date_match = re.search(
        r"(?:on\s+)?(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})",
        text,
        re.IGNORECASE,
    )
    if date_match:
        metadata["mint_date"] = date_match.group(1)

    # Deadline detection
    deadline_match = re.search(
        r"(?:deadline|closes?|ends?|last day)\s*(?:is|:)?\s*(.+?)(?:\.|$)",
        text,
        re.IGNORECASE,
    )
    if deadline_match:
        metadata["whitelist_deadline"] = deadline_match.group(1).strip()

    return metadata


class PostParser:
    """Parses posts for Arc NFT whitelist relevance."""

    def parse(self, post: Post) -> ScoredPost:
        """Parse a post and return a ScoredPost with all detections."""
        text = post.text

        # Detect relevance
        is_arc = detect_arc_relevance(text)
        is_nft = detect_nft_relevance(text)
        is_whitelist = detect_whitelist_relevance(text)

        # Extract URLs
        classified_urls = extract_and_classify_urls(post)

        # Detect project info
        project_name = detect_project_name(post)
        project_username = detect_project_username(post)

        # Extract metadata
        metadata = extract_metadata(post)

        # Build ScoredPost
        scored = ScoredPost(
            post=post,
            is_arc_relevant=is_arc,
            is_nft_relevant=is_nft,
            is_whitelist_relevant=is_whitelist,
            project_name=project_name,
            project_username=project_username,
            classified_urls=classified_urls,
        )

        # Set URLs from classified
        scored.whitelist_url = (
            classified_urls["WHITELIST"][0] if classified_urls["WHITELIST"] else None
        )
        scored.mint_url = (
            classified_urls["MINT"][0] if classified_urls["MINT"] else None
        )
        scored.discord_url = (
            classified_urls["DISCORD"][0] if classified_urls["DISCORD"] else None
        )
        scored.website_url = extract_project_website(classified_urls)

        # Set metadata
        scored.mint_date = metadata.get("mint_date")
        scored.whitelist_deadline = metadata.get("whitelist_deadline")
        scored.supply = metadata.get("supply")
        scored.whitelist_type = metadata.get("whitelist_type")

        return scored
