"""URL extraction and classification."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from models.post import Post, ScoredPost
from scoring.keywords import URL_PATTERNS


# Known domains that are NOT project websites
NON_WEBSITE_DOMAINS = {
    "x.com", "twitter.com", "t.co",
    "discord.gg", "discord.com", "discord.io", "discord.me", "discordapp.com",
    "t.me", "telegram.org",
    "youtube.com", "youtu.be",
    "instagram.com",
    "facebook.com", "fb.com",
    "medium.com",
    "mirror.xyz",
}


def extract_urls(text: str, post_urls: list[str]) -> list[str]:
    """Extract all URLs from post text and metadata."""
    urls = set()

    # From post metadata
    for url in post_urls:
        urls.add(url)

    # From text
    found = re.findall(r"https?://[^\s]+", text)
    for url in found:
        # Clean trailing punctuation
        url = url.rstrip(".,;:!?)")
        urls.add(url)

    # Also look for URLs without http (e.g., "discord.gg/xxx")
    no_scheme = re.findall(r"\b((?:discord|twitter)\.[\w./]+)", text, re.IGNORECASE)
    for url in no_scheme:
        urls.add(f"https://{url}")

    return list(urls)


def classify_url(url: str) -> str:
    """Classify a URL by type."""
    url_lower = url.lower()

    # Check whitelist patterns
    for pattern in URL_PATTERNS["WHITELIST"]:
        if pattern in url_lower:
            return "WHITELIST"

    # Check mint patterns
    for pattern in URL_PATTERNS["MINT"]:
        if pattern in url_lower:
            return "MINT"

    # Check Discord
    for pattern in URL_PATTERNS["DISCORD"]:
        if pattern in url_lower:
            return "DISCORD"

    # Check if it's X/Twitter
    if "x.com" in url_lower or "twitter.com" in url_lower:
        return "X"

    # Otherwise it's a website
    return "WEBSITE"


def extract_and_classify_urls(post: Post) -> dict[str, list[str]]:
    """Extract and classify all URLs from a post."""
    all_urls = extract_urls(post.text, post.urls)
    classified: dict[str, list[str]] = {
        "WHITELIST": [],
        "MINT": [],
        "WEBSITE": [],
        "DISCORD": [],
        "X": [],
        "OTHER": [],
    }

    for url in all_urls:
        category = classify_url(url)
        if category in classified:
            classified[category].append(url)
        else:
            classified["OTHER"].append(url)

    return classified


def extract_project_website(classified_urls: dict[str, list[str]]) -> str | None:
    """Extract the project website URL (not social/media)."""
    for url in classified_urls.get("WEBSITE", []):
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            if domain not in NON_WEBSITE_DOMAINS:
                return url
        except Exception:
            continue
    return None
