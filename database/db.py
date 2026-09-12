"""SQLite database wrapper — async operations via aiosqlite."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from config import Config
from database.models import SCHEMA_SQL


class Database:
    """Async SQLite database wrapper."""

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self.db_path = self._resolve_db_path()
        self._db: aiosqlite.Connection | None = None

    def _resolve_db_path(self) -> str:
        """Resolve database file path."""
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        return str(data_dir / "arc_wl.db")

    def _log(self, level: str, msg: str) -> None:
        """Safe log — handles None logger."""
        if self.logger:
            getattr(self.logger, level, lambda m: None)(msg)

    async def initialize(self) -> None:
        """Initialize database connection and schema."""
        self._log("info", f"Initializing database: {self.db_path}")
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA_SQL)
        await self._db.commit()
        self._log("info", "Database initialized successfully.")

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def is_open(self) -> bool:
        return self._db is not None

    # ── Posts ──────────────────────────────────────────

    async def tweet_exists(self, tweet_id: str) -> bool:
        """Check if a tweet already exists in the database."""
        if not self._db:
            return False
        cursor = await self._db.execute(
            "SELECT 1 FROM posts WHERE tweet_id = ?", (tweet_id,)
        )
        row = await cursor.fetchone()
        return row is not None

    async def insert_post(
        self,
        *,
        tweet_id: str,
        author_username: str,
        author_display_name: str | None = None,
        text: str = "",
        tweet_url: str = "",
        created_at: str | None = None,
        project_name: str | None = None,
        project_username: str | None = None,
        relevance_score: int = 0,
        priority: str = "IGNORE",
        whitelist_url: str | None = None,
        mint_url: str | None = None,
        website_url: str | None = None,
        discord_url: str | None = None,
        mint_date: str | None = None,
        whitelist_deadline: str | None = None,
        supply: str | None = None,
        whitelist_type: str | None = None,
        notified: bool = False,
    ) -> bool:
        """Insert a post. Returns True if inserted, False if duplicate."""
        if not self._db:
            raise RuntimeError("Database not initialized")

        # Dedup check
        if await self.tweet_exists(tweet_id):
            return False

        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """INSERT INTO posts (
                tweet_id, author_username, author_display_name,
                text, tweet_url, created_at, detected_at,
                project_name, project_username,
                relevance_score, priority,
                whitelist_url, mint_url, website_url, discord_url,
                mint_date, whitelist_deadline, supply, whitelist_type,
                notified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tweet_id, author_username, author_display_name,
                text, tweet_url, created_at, now,
                project_name, project_username,
                relevance_score, priority,
                whitelist_url, mint_url, website_url, discord_url,
                mint_date, whitelist_deadline, supply, whitelist_type,
                int(notified),
            ),
        )
        await self._db.commit()
        return True

    async def mark_notified(self, tweet_id: str) -> None:
        """Mark a post as notified."""
        if not self._db:
            return
        await self._db.execute(
            "UPDATE posts SET notified = 1 WHERE tweet_id = ?", (tweet_id,)
        )
        await self._db.commit()

    # ── Searches ───────────────────────────────────────

    async def log_search(
        self,
        query: str,
        results_count: int,
        new_results_count: int,
    ) -> None:
        """Log a search execution."""
        if not self._db:
            return
        await self._db.execute(
            """INSERT INTO searches (query, results_count, new_results_count)
               VALUES (?, ?, ?)""",
            (query, results_count, new_results_count),
        )
        await self._db.commit()

    # ── Projects ───────────────────────────────────────

    async def upsert_project(
        self,
        *,
        name: str | None = None,
        x_username: str | None = None,
        website: str | None = None,
    ) -> None:
        """Insert or update a project."""
        if not self._db:
            return

        now = datetime.now(timezone.utc).isoformat()

        # Try to find existing by username or name
        existing_id = None
        if x_username:
            cursor = await self._db.execute(
                "SELECT id FROM projects WHERE x_username = ?", (x_username,)
            )
            row = await cursor.fetchone()
            if row:
                existing_id = row["id"]

        if not existing_id and name:
            cursor = await self._db.execute(
                "SELECT id FROM projects WHERE name = ?", (name,)
            )
            row = await cursor.fetchone()
            if row:
                existing_id = row["id"]

        if existing_id:
            await self._db.execute(
                "UPDATE projects SET last_detected_at = ? WHERE id = ?",
                (now, existing_id),
            )
        else:
            await self._db.execute(
                """INSERT INTO projects (name, x_username, website, first_detected_at, last_detected_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, x_username, website, now, now),
            )
        await self._db.commit()

    # ── Stats ──────────────────────────────────────────

    async def get_stats(self) -> dict:
        """Get database statistics."""
        if not self._db:
            return {}

        stats = {}

        cursor = await self._db.execute("SELECT COUNT(*) as cnt FROM posts")
        stats["total_posts"] = (await cursor.fetchone())["cnt"]

        cursor = await self._db.execute(
            "SELECT COUNT(*) as cnt FROM posts WHERE priority = 'HIGH'"
        )
        stats["high_priority"] = (await cursor.fetchone())["cnt"]

        cursor = await self._db.execute(
            "SELECT COUNT(*) as cnt FROM posts WHERE priority = 'MEDIUM'"
        )
        stats["medium_priority"] = (await cursor.fetchone())["cnt"]

        cursor = await self._db.execute(
            "SELECT COUNT(*) as cnt FROM posts WHERE notified = 1"
        )
        stats["notified"] = (await cursor.fetchone())["cnt"]

        cursor = await self._db.execute("SELECT COUNT(*) as cnt FROM searches")
        stats["total_searches"] = (await cursor.fetchone())["cnt"]

        cursor = await self._db.execute("SELECT COUNT(*) as cnt FROM projects")
        stats["total_projects"] = (await cursor.fetchone())["cnt"]

        cursor = await self._db.execute(
            "SELECT COUNT(*) as cnt FROM posts WHERE detected_at >= datetime('now', '-24 hours')"
        )
        stats["posts_last_24h"] = (await cursor.fetchone())["cnt"]

        return stats

    async def get_recent_posts(self, limit: int = 20) -> list[dict]:
        """Get recent posts."""
        if not self._db:
            return []
        cursor = await self._db.execute(
            """SELECT * FROM posts ORDER BY detected_at DESC LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
