"""Test deduplication service."""
from __future__ import annotations

import logging
import pytest
import pytest_asyncio
import os
import tempfile
from config import Config
from database.db import Database
from services.dedup import Deduplicator
from models.post import Post

_logger = logging.getLogger("test_dedup")


@pytest_asyncio.fixture
async def dedup():
    """Create a deduplicator with temp database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        db = Database(config, _logger)
        db.db_path = os.path.join(tmpdir, "test.db")
        await db.initialize()
        deduplicator = Deduplicator(db, _logger)
        yield deduplicator, db
        await db.close()


@pytest.mark.asyncio
async def test_is_duplicate(dedup):
    deduplicator, db = dedup

    assert await deduplicator.is_duplicate("nonexistent") is False

    await db.insert_post(tweet_id="exists1", author_username="u1")
    assert await deduplicator.is_duplicate("exists1") is True


@pytest.mark.asyncio
async def test_filter_new(dedup):
    deduplicator, db = dedup

    posts = [
        Post(tweet_id="new1", author_username="u1", text="New post 1"),
        Post(tweet_id="new2", author_username="u2", text="New post 2"),
    ]

    new = await deduplicator.filter_new(posts)
    assert len(new) == 2

    # Insert one, then filter again
    await db.insert_post(tweet_id="new1", author_username="u1")
    new = await deduplicator.filter_new(posts)
    assert len(new) == 1
    assert new[0].tweet_id == "new2"
