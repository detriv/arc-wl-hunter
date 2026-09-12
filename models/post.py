"""Post data model — normalized representation of an X post."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Post:
    """Normalized post/tweet model."""

    tweet_id: str
    author_username: str
    author_display_name: str | None = None
    text: str = ""
    tweet_url: str = ""
    created_at: datetime | None = None
    urls: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure lists are never None."""
        if self.urls is None:
            self.urls = []
        if self.hashtags is None:
            self.hashtags = []
        if self.mentions is None:
            self.mentions = []


@dataclass
class ScoredPost:
    """Post with relevance scoring attached."""

    post: Post
    score: int = 0
    priority: str = "IGNORE"  # HIGH, MEDIUM, IGNORE
    is_arc_relevant: bool = False
    is_nft_relevant: bool = False
    is_whitelist_relevant: bool = False
    project_name: str | None = None
    project_username: str | None = None
    website_url: str | None = None
    whitelist_url: str | None = None
    mint_url: str | None = None
    discord_url: str | None = None
    mint_date: str | None = None
    whitelist_deadline: str | None = None
    supply: str | None = None
    whitelist_type: str | None = None
    classified_urls: dict[str, list[str]] = field(default_factory=dict)
