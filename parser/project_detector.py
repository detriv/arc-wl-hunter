"""Project detection from post data."""
from __future__ import annotations

import re

from models.post import Post


def detect_project_name(post: Post) -> str | None:
    """Attempt to detect the NFT project name."""
    text = post.text

    # Pattern: "Project Name" + NFT/collection keywords
    patterns = [
        # "X NFT collection" or "X NFTs"
        r"([A-Z][\w\s&]+?)\s+(?:NFTs?|collection|collection)",
        # "X is launching" or "X presents"
        r"([A-Z][\w\s&]+?)\s+(?:is\s+)?(?:launching|presenting|dropping)",
        # "introducing X"
        r"(?:introducing|meet|presenting)\s+([A-Z][\w\s&]+?)(?:\s*[-–—:,])",
        # Project name in quotes
        r'"([^"]+)"\s+(?:NFT|collection|mint|whitelist)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 50:
                return name

    # Use display name if it looks like a project
    if post.author_display_name:
        name_lower = post.author_display_name.lower()
        project_indicators = ["nft", "dao", "labs", "studio", "art", "club", "punk", "ape"]
        if any(ind in name_lower for ind in project_indicators):
            return post.author_display_name.strip()

    return None


def detect_project_username(post: Post) -> str | None:
    """Get the project's X username (usually the author)."""
    if post.author_username:
        return post.author_username
    return None
