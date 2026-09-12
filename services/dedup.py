"""Deduplication service."""
from __future__ import annotations

import logging

from database.db import Database


class Deduplicator:
    """Handles post deduplication using the database."""

    def __init__(self, db: Database, logger: logging.Logger) -> None:
        self.db = db
        self.logger = logger

    async def is_duplicate(self, tweet_id: str) -> bool:
        """Check if a tweet is a duplicate."""
        return await self.db.tweet_exists(tweet_id)

    async def filter_new(self, posts: list) -> list:
        """Filter out duplicate posts, return only new ones."""
        new_posts = []
        for post in posts:
            if not await self.is_duplicate(post.tweet_id):
                new_posts.append(post)
            else:
                self.logger.debug(f"Skipping duplicate: {post.tweet_id}")
        return new_posts
