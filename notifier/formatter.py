"""Telegram message formatter — uses HTML parse mode."""
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


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _link(url: str, label: str | None = None) -> str:
    """Create an HTML link."""
    return f'<a href="{_esc(url)}">{_esc(label or url)}</a>'


def format_high_alert(post: ScoredPost) -> str:
    """Format a HIGH priority alert message."""
    lines = ["🔥 <b>ARC NFT WHITELIST DETECTED</b>", ""]

    # Project info
    project = post.project_name or post.project_username or "Unknown Project"
    lines.append(f"📌 Project: {_esc(project)}")
    lines.append(f"👤 Author: @{_esc(post.post.author_username)}")
    lines.append("")

    # Score
    lines.append(f"⭐ Priority: <b>HIGH</b>")
    lines.append(f"📊 Score: <b>{post.score}</b>")
    lines.append("")

    # Post text
    text = post.post.text[:300] + ("..." if len(post.post.text) > 300 else "")
    lines.append("📝 Post:")
    lines.append(_esc(text))
    lines.append("")

    # URLs
    if post.whitelist_url:
        lines.append(f"🎟 Whitelist: {_link(post.whitelist_url)}")
    if post.mint_url:
        lines.append(f"⛏ Mint: {_link(post.mint_url)}")
    if post.website_url:
        lines.append(f"🌐 Website: {_link(post.website_url)}")
    if post.discord_url:
        lines.append(f"💬 Discord: {_link(post.discord_url)}")

    # Metadata
    if post.whitelist_type:
        lines.append(f"🏷 Type: {_esc(post.whitelist_type)}")
    if post.supply:
        lines.append(f"📦 Supply: {_esc(post.supply)}")
    if post.mint_date:
        lines.append(f"📅 Mint Date: {_esc(post.mint_date)}")
    if post.whitelist_deadline:
        lines.append(f"⏰ Deadline: {_esc(post.whitelist_deadline)}")

    lines.append("")

    # Tweet link
    if post.post.tweet_url:
        lines.append(f"🔗 X Post: {_link(post.post.tweet_url)}")

    # Timestamp
    ts = _format_timestamp(post.post.created_at)
    lines.append(f"🕐 Posted: {ts}")

    return "\n".join(lines)


def format_medium_alert(post: ScoredPost) -> str:
    """Format a MEDIUM priority alert message."""
    lines = ["🟡 <b>ARC NFT OPPORTUNITY</b>", ""]

    # Project info
    project = post.project_name or post.project_username or "Unknown Project"
    lines.append(f"📌 Project: {_esc(project)}")
    lines.append(f"👤 Author: @{_esc(post.post.author_username)}")
    lines.append("")

    # Score
    lines.append(f"📊 Score: <b>{post.score}</b>")
    lines.append("")

    # Post text
    text = post.post.text[:250] + ("..." if len(post.post.text) > 250 else "")
    lines.append("📝 Post:")
    lines.append(_esc(text))
    lines.append("")

    # URLs (only key ones)
    if post.whitelist_url:
        lines.append(f"🎟 Whitelist: {_link(post.whitelist_url)}")
    if post.mint_url:
        lines.append(f"⛏ Mint: {_link(post.mint_url)}")
    if post.discord_url:
        lines.append(f"💬 Discord: {_link(post.discord_url)}")

    # Metadata
    if post.whitelist_type:
        lines.append(f"🏷 Type: {_esc(post.whitelist_type)}")

    lines.append("")

    # Tweet link
    if post.post.tweet_url:
        lines.append(f"🔗 X Post: {_link(post.post.tweet_url)}")

    # Timestamp
    ts = _format_timestamp(post.post.created_at)
    lines.append(f"🕐 Posted: {ts}")

    return "\n".join(lines)


def format_test_message() -> str:
    """Format a test message."""
    return (
        "✅ <b>Arc NFT Whitelist Hunter</b>\n"
        "\n"
        "Telegram connection is working!\n"
        "\n"
        "You will receive alerts here when Arc NFT whitelist opportunities are detected."
    )
