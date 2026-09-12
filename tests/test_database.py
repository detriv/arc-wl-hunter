"""Test database operations."""
from __future__ import annotations

import asyncio
import logging
import os
import pytest
import pytest_asyncio
import tempfile
from config import Config
from database.db import Database

_logger = logging.getLogger("test_db")


@pytest_asyncio.fixture
async def db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config()
        test_db_path = os.path.join(tmpdir, "test.db")
        database = Database(config, _logger)
        database.db_path = test_db_path
        await database.initialize()
        yield database
        await database.close()


@pytest.mark.asyncio
async def test_insert_and_retrieve(db):
    """Test basic insert and retrieval."""
    inserted = await db.insert_post(
        tweet_id="test1",
        author_username="user1",
        text="Test post",
        relevance_score=85,
        priority="HIGH",
    )
    assert inserted is True

    exists = await db.tweet_exists("test1")
    assert exists is True


@pytest.mark.asyncio
async def test_deduplication(db):
    """Test that duplicate tweet_ids are rejected."""
    await db.insert_post(tweet_id="dedup1", author_username="user1", text="First")

    inserted = await db.insert_post(
        tweet_id="dedup1", author_username="user2", text="Duplicate"
    )
    assert inserted is False


@pytest.mark.asyncio
async def test_mark_notified(db):
    """Test marking a post as notified."""
    await db.insert_post(tweet_id="notify1", author_username="user1")
    await db.mark_notified("notify1")

    stats = await db.get_stats()
    assert stats["notified"] == 1


@pytest.mark.asyncio
async def test_log_search(db):
    """Test search logging."""
    await db.log_search("test query", 10, 3)

    stats = await db.get_stats()
    assert stats["total_searches"] == 1


@pytest.mark.asyncio
async def test_upsert_project(db):
    """Test project upsert."""
    await db.upsert_project(name="Test Project", x_username="testuser")

    stats = await db.get_stats()
    assert stats["total_projects"] == 1

    # Upsert same project again
    await db.upsert_project(name="Test Project", x_username="testuser")
    stats = await db.get_stats()
    assert stats["total_projects"] == 1  # Still 1


@pytest.mark.asyncio
async def test_get_stats(db):
    """Test statistics retrieval."""
    await db.insert_post(
        tweet_id="s1", author_username="u1",
        relevance_score=90, priority="HIGH",
    )
    await db.insert_post(
        tweet_id="s2", author_username="u2",
        relevance_score=65, priority="MEDIUM",
    )
    await db.insert_post(
        tweet_id="s3", author_username="u3",
        relevance_score=20, priority="IGNORE",
    )

    stats = await db.get_stats()
    assert stats["total_posts"] == 3
    assert stats["high_priority"] == 1
    assert stats["medium_priority"] == 1


@pytest.mark.asyncio
async def test_get_recent_posts(db):
    """Test recent posts retrieval."""
    for i in range(5):
        await db.insert_post(tweet_id=f"r{i}", author_username=f"u{i}")

    recent = await db.get_recent_posts(3)
    assert len(recent) == 3
