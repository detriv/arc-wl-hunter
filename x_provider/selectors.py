"""X/Twitter DOM selectors — isolated for easy maintenance.

If X changes its UI, update selectors here.
"""
from __future__ import annotations

# ── Article / Tweet container ──────────────────────
ARTICLE_SELECTOR = "article[data-testid='tweet']"

# ── Tweet text ─────────────────────────────────────
TEXT_SELECTOR = "div[data-testid='tweetText']"

# ── User info ──────────────────────────────────────
USER_NAME_SELECTOR = "div[data-testid='User-Name']"
USERNAME_LINK_SELECTOR = "a[role='link'][href^='/']"

# ── Tweet link ─────────────────────────────────────
TIME_SELECTOR = "time"
TWEET_LINK_SELECTOR = "a[href*='/status/']"

# ── Search ─────────────────────────────────────────
SEARCH_INPUT_SELECTOR = "input[data-testid='SearchBox_Search_Input']"
SEARCH_BUTTON_SELECTOR = "div[data-testid='searchButton']"

# ── Login detection ────────────────────────────────
LOGIN_AVATAR_SELECTOR = "div[data-testid='SideNav_AccountSwitcher_Button']"
LOGIN_HEADER_SELECTOR = "a[data-testid='AppTabBar_Home_Link']"

# ── Timeline ───────────────────────────────────────
TIMELINE_SELECTOR = "div[data-testid='primaryColumn']"
