"""Message formatting utilities for worker notifications."""

from __future__ import annotations

import re
from typing import Any

from src.infrastructure.config.settings import get_settings
from src.infrastructure.monitoring.logger import get_logger

logger = get_logger(name="formatters")


def clean_markdown(text: str) -> str:
    """Remove all Markdown formatting characters from text.

    Purpose:
        Aggressively clean text to prevent Telegram Markdown parse errors.
        Removes all Markdown characters including escaped ones.

    Args:
        text: Text to clean

    Returns:
        Cleaned plain text without Markdown characters
    """
    # Remove all Markdown characters multiple times to catch nested/escaped ones
    # First pass: remove standard Markdown chars
    text = re.sub(r'[*_`]', '', text)
    text = re.sub(r'\[', '', text)
    text = re.sub(r'\]', '', text)
    text = re.sub(r'\(', '', text)
    text = re.sub(r'\)', '', text)
    text = re.sub(r'\\', '', text)  # Remove backslashes

    # Second pass: remove any remaining patterns
    text = re.sub(r'\*+', '', text)  # Remove any asterisks (single or multiple)
    text = re.sub(r'_+', '', text)   # Remove any underscores
    text = re.sub(r'`+', '', text)   # Remove any backticks

    # Remove escaped characters explicitly
    text = text.replace('\\*', '').replace('\\_', '').replace('\\`', '')
    text = text.replace('\\[', '').replace('\\]', '')

    # Preserve newlines for readability, but clean them
    text = re.sub(r'\n\n+', '\n\n', text)  # Max 2 newlines
    text = text.strip()

    return text


def format_summary(tasks: list[dict[str, Any]], stats: dict[str, Any], debug: bool = False) -> str:
    """Format task summary message.

    Purpose:
        Create formatted task summary message for morning notifications.
        Supports both normal and debug modes.

    Args:
        tasks: List of task dictionaries
        stats: Statistics dictionary with total, completed, overdue, high_priority
        debug: If True, use debug header instead of morning greeting

    Returns:
        Formatted summary message text
    """
    logger.info("format_summary called", 
                tasks_count=len(tasks) if tasks else 0, 
                stats_total=stats.get('total', 0), 
                debug=debug)

    if not tasks or len(tasks) == 0:
        if debug:
            return (f"🔍 *Debug Summary (Last 24h)*\n\n"
                    f"📊 No active tasks found (checked {stats.get('total', 0)} tasks).")
        header = "🌅 *Good morning!*\n\n"
        return f"{header}No tasks found. Enjoy your day!"

    header = ("🔍 *Debug Summary (Last 24h)*\n\n" 
              if debug else "🌅 *Good morning!*\n\n")
    text = f"{header}📊 Tasks: {stats.get('total', 0)}\n"
    
    if stats.get("high_priority", 0) > 0:
        text += f"🔴 High priority: {stats['high_priority']}\n"
    
    text += "\n*Your tasks:*\n\n"
    for task in tasks[:5]:
        emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            task.get("priority", "medium"), "⚪")
        text += f"{emoji} {task.get('title', 'Untitled')}\n"
    
    if len(tasks) > 5:
        text += f"\n_...and {len(tasks) - 5} more_"
    
    return text


def format_single_digest(digest: dict[str, Any], debug: bool = False) -> str:
    """Format single channel digest message with Russian localization.

    Purpose:
        Create formatted digest message for one channel.
        Returns plain text without Markdown to avoid parsing errors.

    Args:
        digest: Single digest dict with channel, summary, post_count, tags
        debug: If True, use debug header

    Returns:
        Formatted digest message text (plain text, no Markdown)
    """
    settings = get_settings()
    
    channel = digest.get("channel", "unknown")
    summary = digest.get("summary", "")
    post_count = digest.get("post_count", 0)
    tags = digest.get("tags", [])

    # Aggressively clean summary - remove ALL Markdown characters
    summary_clean = clean_markdown(summary)

    # Enforce max_chars from settings - Telegram message limit is 4096
    max_chars = settings.digest_summary_max_chars
    # Additional safety: never exceed 2500 chars
    absolute_max = min(max_chars, 2500)

    if len(summary_clean) > absolute_max:
        # Try to truncate at sentence boundary
        truncated = summary_clean[:absolute_max]
        last_period = truncated.rfind('.')
        if last_period > absolute_max * 0.7:  # If period is in last 30%, use it
            summary_clean = truncated[:last_period + 1]
        else:
            summary_clean = truncated + "..."
            logger.warning("Summary truncated at hard limit", 
                          original_length=len(summary), 
                          truncated_length=len(summary_clean))

    # Format with tags if available (no Markdown)
    tags_str = ""
    if tags:
        tags_str = f"\nТеги: {', '.join(f'#{tag}' for tag in tags[:5])}"

    # Build detailed message
    header = ("📰 Дайджест канала\n\n" 
              if not debug else "📰 Debug Digest (Last 7 days)\n\n")
    text = f"{header}"
    text += f"📌 {channel}\n"
    text += f"📊 Постов: {post_count}"
    if tags_str:
        text += tags_str
    text += f"\n\n{summary_clean}\n"

    # Final safety check - remove any Markdown that might have slipped through
    text = clean_markdown(text)

    return text


def format_digest(digests: list[dict[str, Any]], debug: bool = False) -> str:
    """Format channel digest message with Russian localization (legacy method).

    Purpose:
        Create formatted digest message for multiple channels.
        Returns plain text without Markdown to avoid parsing errors.

    Args:
        digests: List of digest dictionaries
        debug: If True, use debug header

    Returns:
        Formatted digest message text (plain text, no Markdown)
    """
    settings = get_settings()

    header = ("📰 Debug Digest (Last 7 days)\n\n" 
              if debug else "📰 Дайджест каналов\n\n")
    text = header

    # Use configurable max channels
    max_channels = settings.digest_max_channels
    max_chars = settings.digest_summary_max_chars

    # Sort by post_count descending (most active first)
    sorted_digests = sorted(
        digests, 
        key=lambda x: x.get("post_count", 0), 
        reverse=True
    )[:max_channels]

    for digest in sorted_digests:
        channel = digest.get("channel", "unknown")
        summary = digest.get("summary", "")
        post_count = digest.get("post_count", 0)
        tags = digest.get("tags", [])

        # Aggressively clean summary - remove ALL Markdown characters
        summary_clean = clean_markdown(summary)

        # Truncate if too long
        if len(summary_clean) > max_chars:
            summary_clean = summary_clean[:max_chars - 3] + "..."

        # Format with tags if available (no Markdown)
        tags_str = ""
        if tags:
            tags_str = f" {', '.join(f'#{tag}' for tag in tags[:3])}"

        text += f"📌 {channel} ({post_count} постов{tags_str})\n{summary_clean}\n\n"

    if len(digests) > max_channels:
        remaining = len(digests) - max_channels
        text += f"...и еще {remaining} каналов\n\n"

    # Final safety check - remove any Markdown that might have slipped through
    text = clean_markdown(text)

    return text

