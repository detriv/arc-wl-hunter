"""Telegram message formatter."""
from __future__ import annotations

from datetime import datetime

from models.post import ScoredPost


def _format_timestamp(dt: datetime | None) -> str:
    """Format datetime for display."""
    if not dt:
        return "Unknown"
    try:
        return dt.strftime("%d %b %Y %H:%M UTC")
    except Exception:
        return str(dt)


def _escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    special = r"_*[]()~`>#+-=|{}.!"
    for char in special:
        text = text.replace(char, f"\\{char}")
    return text


def format_high_alert(post: ScoredPost) -> str:
    """Format a HIGH priority alert message."""
    lines = [
        "🔥 *ARC NFT WHITELIST DETECTED*",
        "",
    ]

    # Project info
    project = post.project_name or post.project_username or "Unknown Project"
    lines.append(f"📌 Project: {_escape_md(project)}")
    lines.append(f"👤 Author: @{_escape_md(post.post.author_username)}")
    lines.append("")

    # Score
    lines.append(f"⭐ Priority: *HIGH*")
    lines.append(f"📊 Score: *{post.score}*")
    lines.append("")

    # Post text
    text = post.post.text[:300] + ("..." if len(post.post.text) > 300 else "")
    lines.append(f"📝 Post:")
    lines.append(f"{_escape_md(text)}")
    lines.append("")

    # URLs
    if post.whitelist_url:
        lines.append(f"🎟 Whitelist: {post.whitelist_url}")
    if post.mint_url:
        lines.append(f"⛏ Mint: {post.mint_url}")
    if post.website_url:
        lines.append(f"🌐 Website: {post.website_url}")
    if post.discord_url:
        lines.append(f"💬 Discord: {post.discord_url}")

    # Metadata
    if post.whitelist_type:
        lines.append(f"🏷 Type: {_escape_md(post.whitelist_type)}")
    if post.supply:
        lines.append(f"📦 Supply: {_escape_md(post.supply)}")
    if post.mint_date:
        lines.append(f"📅 Mint Date: {_escape_md(post.mint_date)}")
    if post.whitelist_deadline:
        lines.append(f"⏰ Deadline: {_escape_md(post.whitelist_deadline)}")

    lines.append("")

    # Tweet link
    if post.post.tweet_url:
        lines.append(f"🔗 X Post: {post.post.tweet_url}")

    # Timestamp
    ts = _format_timestamp(post.post.created_at)
    lines.append(f"🕐 Posted: {ts}")

    return "\n".join(lines)


def format_medium_alert(post: ScoredPost) -> str:
    """Format a MEDIUM priority alert message."""
    lines = [
        "🟡 *ARC NFT OPPORTUNITY*",
        "",
    ]

    # Project info
    project = post.project_name or post.project_username or "Unknown Project"
    lines.append(f"📌 Project: {_escape_md(project)}")
    lines.append(f"👤 Author: @{_escape_md(post.post.author_username)}")
    lines.append("")

    # Score
    lines.append(f"📊 Score: *{post.score}*")
    lines.append("")

    # Post text
    text = post.post.text[:250] + ("..." if len(post.post.text) > 250 else "")
    lines.append(f"📝 Post:")
    lines.append(f"{_escape_md(text)}")
    lines.append("")

    # URLs (only key ones)
    if post.whitelist_url:
        lines.append(f"🎟 Whitelist: {post.whitelist_url}")
    if post.mint_url:
        lines.append(f"⛏ Mint: {post.mint_url}")
    if post.discord_url:
        lines.append(f"💬 Discord: {post.discord_url}")

    # Metadata
    if post.whitelist_type:
        lines.append(f"🏷 Type: {_escape_md(post.whitelist_type)}")

    lines.append("")

    # Tweet link
    if post.post.tweet_url:
        lines.append(f"🔗 X Post: {post.post.tweet_url}")

    # Timestamp
    ts = _format_timestamp(post.post.created_at)
    lines.append(f"🕐 Posted: {ts}")

    return "\n".join(lines)


def format_test_message() -> str:
    """Format a test message."""
    return (
        "✅ *Arc NFT Whitelist Hunter*\n"
        "\n"
        "Telegram connection is working!\n"
        "\n"
        "You will receive alerts here when Arc NFT whitelist opportunities are detected."
    )
