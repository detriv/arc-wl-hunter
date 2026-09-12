"""Keyword definitions for relevance detection."""
from __future__ import annotations

# ── Arc Network keywords ────────────────────────────
ARC_KEYWORDS: list[str] = [
    "arc network",
    "arc.network",
    "@arc",
    "arc blockchain",
    "arc chain",
    "on arc",
    "launching on arc",
    "built on arc",
    "arc ecosystem",
]

# ── NFT keywords ────────────────────────────────────
NFT_KEYWORDS: list[str] = [
    "nft",
    "nfts",
    "nft collection",
    "collection",
    "mint",
    "minting",
    "drop",
    "nft launch",
    "nft drop",
    "genesis",
    "gen",
]

# ── Whitelist keywords ──────────────────────────────
WHITELIST_KEYWORDS: list[str] = [
    "whitelist",
    "wl",
    "allowlist",
    "allow list",
    "whitelisted",
    "whitelist spot",
    "wl spot",
    "wl spots",
    "wl application",
    "wl form",
]

# ── Allocation keywords ─────────────────────────────
ALLOCATION_KEYWORDS: list[str] = [
    "gtd",
    "fcfs",
    "guaranteed",
    "guaranteed spot",
    "allocation",
    "allocation spot",
    "og spot",
    "og list",
    "priority access",
    "early access",
]

# ── Application keywords ────────────────────────────
APPLICATION_KEYWORDS: list[str] = [
    "apply",
    "application",
    "register",
    "registration",
    "form",
    "join",
    "claim",
    "sign up",
    "signup",
]

# ── Negative keywords (reduce score) ────────────────
NEGATIVE_KEYWORDS: list[str] = [
    "price",
    "trading",
    "buy",
    "sell",
    "pump",
    "dump",
    "chart",
    "market cap",
    "marketcap",
    "token price",
    "airdrop"  # generic airdrop without NFT context
]

# ── URL classification patterns ─────────────────────
URL_PATTERNS: dict[str, list[str]] = {
    "WHITELIST": [
        "/whitelist", "whitelist.", "wl.", "allowlist",
        "wl-form", "wl_signup", "whitelist-form",
    ],
    "MINT": [
        "/mint", "mint.", "mintnow", "mint-now",
    ],
    "DISCORD": [
        "discord.gg", "discord.com/invite", "discord.io",
        "discord.me", "discordapp.com/invite",
    ],
    "WEBSITE": [
        "http", "https",
    ],
}
