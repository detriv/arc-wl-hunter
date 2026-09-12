"""SQLite database schema and initialization."""
from __future__ import annotations

SCHEMA_SQL = """
-- Posts table: stores all detected posts
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tweet_id TEXT UNIQUE NOT NULL,
    author_username TEXT NOT NULL,
    author_display_name TEXT,
    text TEXT,
    tweet_url TEXT,
    created_at TEXT,
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    project_name TEXT,
    project_username TEXT,
    relevance_score INTEGER DEFAULT 0,
    priority TEXT DEFAULT 'IGNORE',
    whitelist_url TEXT,
    mint_url TEXT,
    website_url TEXT,
    discord_url TEXT,
    mint_date TEXT,
    whitelist_deadline TEXT,
    supply TEXT,
    whitelist_type TEXT,
    notified INTEGER DEFAULT 0,
    created_db_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Searches table: tracks search executions
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    executed_at TEXT NOT NULL DEFAULT (datetime('now')),
    results_count INTEGER DEFAULT 0,
    new_results_count INTEGER DEFAULT 0
);

-- Projects table: detected projects
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    x_username TEXT,
    website TEXT,
    first_detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_detected_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_posts_tweet_id ON posts(tweet_id);
CREATE INDEX IF NOT EXISTS idx_posts_priority ON posts(priority);
CREATE INDEX IF NOT EXISTS idx_posts_detected_at ON posts(detected_at);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_username);
CREATE INDEX IF NOT EXISTS idx_posts_notified ON posts(notified);
CREATE INDEX IF NOT EXISTS idx_searches_executed_at ON searches(executed_at);
CREATE INDEX IF NOT EXISTS idx_projects_username ON projects(x_username);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
"""

# Migration tracking
MIGRATIONS: list[str] = []
