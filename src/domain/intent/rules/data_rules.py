"""Data intent classification rules.

Patterns for digest requests, subscription management, and statistics.
Migrated from DataHandler patterns with entity extraction.
Following Python Zen: Simple is better than complex.
"""

import re
from typing import Callable, Dict, Tuple

from src.domain.intent.intent_classifier import IntentType


def extract_channel_name(match: re.Match) -> str:
    """Extract channel name from match (assumes channel is in group 1).

    Args:
        match: Regex match object

    Returns:
        Channel username (without @) or empty string
    """
    if match.lastindex >= 1:
        channel = match.group(1).strip().lstrip("@")
        # Normalize Russian genitive forms
        if channel.lower().endswith("и") and len(channel) > 2:
            if re.search(r"[а-яА-Я]", channel):
                channel = channel[:-1] + "а"
        elif channel.lower().endswith("е") and len(channel) > 2:
            if re.search(r"[а-яА-Я]", channel):
                channel = channel[:-1] + "а"
        return channel
    return ""


def extract_channel_from_subscription(match: re.Match) -> str:
    """Extract channel name from subscription pattern (channel is in group 2).

    Args:
        match: Regex match object where group(1) is verb, group(2) is channel

    Returns:
        Channel username (without @) or empty string
    """
    if match.lastindex >= 2:
        channel = match.group(2).strip().lstrip("@")
        # Normalize Russian genitive forms
        if channel.lower().endswith("и") and len(channel) > 2:
            if re.search(r"[а-яА-Я]", channel):
                channel = channel[:-1] + "а"
        elif channel.lower().endswith("е") and len(channel) > 2:
            if re.search(r"[а-яА-Я]", channel):
                channel = channel[:-1] + "а"
        return channel
    return ""


def extract_days(match: re.Match) -> int:
    """Extract number of days from match.

    Args:
        match: Regex match object

    Returns:
        Number of days (default: 7)
    """
    if match.lastindex >= 1:
        try:
            days = int(match.group(1))
            # Check if it's weeks
            pattern_str = match.re.pattern
            if "week" in pattern_str.lower():
                return days * 7
            return days
        except (ValueError, IndexError):
            pass
    # Check for fixed patterns like "неделю" (7 days)
    if re.search(r"неделю|недели|week", match.group(0), re.IGNORECASE):
        return 7
    return 7  # Default


def extract_job_id(match: re.Match) -> str:
    """Extract job_id from match (UUID-like or alphanumeric ID).

    Args:
        match: Regex match object

    Returns:
        Job ID string or empty string
    """
    if match.lastindex >= 1:
        job_id = match.group(1).strip()
        # Validate it looks like an ID (alphanumeric, hyphens, underscores)
        if re.match(r"^[a-zA-Z0-9_-]+$", job_id):
            return job_id
    return ""


def extract_archive_name(match: re.Match) -> str:
    """Extract archive_name from match (contains .zip or name pattern).

    Args:
        match: Regex match object

    Returns:
        Archive name string or empty string
    """
    if match.lastindex >= 1:
        archive = match.group(1).strip()
        # Check if it contains .zip or matches name_pattern (Name_Name_hw2)
        if ".zip" in archive.lower() or re.search(r"[а-яА-Яa-zA-Z]+_[а-яА-Яa-zA-Z]+_hw\d+", archive, re.IGNORECASE):
            return archive
    return ""


def extract_submission_identifier(match: re.Match) -> Dict[str, str]:
    """Extract submission identifier (job_id, archive_name, or commit_hash).

    Args:
        match: Regex match object where group(1) is the identifier

    Returns:
        Dictionary with appropriate key (job_id, archive_name, or commit_hash)
    """
    if match.lastindex >= 1:
        identifier = match.group(1).strip()
        
        # Check if it's a commit hash (hex, 7+ chars)
        if re.match(r"^[a-f0-9]{7,}$", identifier, re.IGNORECASE):
            return {"commit_hash": identifier}
        
        # Check if it's a UUID-like job_id
        if re.match(r"^[a-zA-Z0-9_-]{8,}$", identifier) and ".zip" not in identifier.lower():
            return {"job_id": identifier}
        
        # Check if it's an archive name
        if ".zip" in identifier.lower() or re.search(r"[а-яА-Яa-zA-Z]+_[а-яА-Яa-zA-Z]+_hw\d+", identifier, re.IGNORECASE):
            return {"archive_name": identifier}
        
        # Default to archive_name if it has underscores (likely name_pattern)
        if "_" in identifier:
            return {"archive_name": identifier}
    
    return {}


def extract_assignment(match: re.Match) -> str:
    """Extract assignment name from match (HW2, HW3, etc.).

    Args:
        match: Regex match object

    Returns:
        Assignment name (e.g., "HW2") or empty string
    """
    if match.lastindex >= 1:
        assignment = match.group(1).strip().upper()
        # Validate it matches HW pattern
        if re.match(r"^HW\d+$", assignment):
            return assignment
    return ""


STOP_WORDS = {
    "за",
    "на",
    "по",
    "дн",
    "дня",
    "дней",
    "день",
    "days",
    "day",
    "of",
    "for",
    "the",
    "a",
    "an",
    "in",
    "at",
    "on",
    "to",
    "from",
    "канала",
    "channel",
    "channels",
    "digest",
    "дайджест",
}

DATA_RULES: list[Tuple[re.Pattern, IntentType, float, Dict[str, Callable]]] = [
    # Subscription list patterns
    (
        re.compile(
            r"(мои|my|all my|все мои|give me|дай|покажи|show|list)\s+(подписк|subscription|канал|channels)",
            re.IGNORECASE,
        ),
        IntentType.DATA_SUBSCRIPTION_LIST,
        0.95,
        {},
    ),
    # Subscription add patterns
    # Match: "подпишись", "подпиш", "подпис", "subscribe", "добавь", "добав", "add"
    (
        re.compile(
            r"(подпишись|подпиш[иь]|подпис[атьь]|subscribe|добавь|добав|add)\s+(?:на|to)?\s*@?([a-zA-Zа-яА-Я0-9_]+)", re.IGNORECASE
        ),
        IntentType.DATA_SUBSCRIPTION_ADD,
        0.95,
        {"channel_username": extract_channel_from_subscription},
    ),
    # Subscription remove patterns
    (
        re.compile(
            r"(отпис|unsubscribe|удал|remove|убери)\s+(?:от|from)?\s*@?([a-zA-Zа-яА-Я0-9_]+)",
            re.IGNORECASE,
        ),
        IntentType.DATA_SUBSCRIPTION_REMOVE,
        0.95,
        {"channel_name_hint": extract_channel_from_subscription},
    ),
    # Digest patterns (with channel and days extraction)
    (
        re.compile(r"дайджест\s+(?:канала\s+)?по\s+([a-zA-Zа-яА-Я0-9_]+)", re.IGNORECASE),
        IntentType.DATA_DIGEST,
        0.95,
        {"channel_name": extract_channel_name},
    ),
    (
        re.compile(r"по\s+([a-zA-Zа-яА-Я0-9_]+)\s+за\s+(\d+)\s+дн", re.IGNORECASE),
        IntentType.DATA_DIGEST,
        0.95,
        {"channel_name": extract_channel_name, "days": extract_days},
    ),
    (
        re.compile(r"дайджест\s+(?:канала\s+)?([a-zA-Zа-яА-Я0-9_]+)", re.IGNORECASE),
        IntentType.DATA_DIGEST,
        0.90,
        {"channel_name": extract_channel_name},
    ),
    (
        # More specific: "digest of CHANNEL" where CHANNEL is not a stop word
        re.compile(r"digest\s+(?:of|for)\s+(?!(?:of|for|the|a|an|канала|channel)\s)([a-zA-Zа-яА-Я0-9_]{2,})", re.IGNORECASE),
        IntentType.DATA_DIGEST,
        0.95,
        {"channel_name": extract_channel_name},
    ),
    (
        re.compile(r"digest\s+(?:of|for)\s+([a-zA-Zа-яА-Я0-9_]+)\s+for\s+(\d+)\s+days?", re.IGNORECASE),
        IntentType.DATA_DIGEST,
        0.95,
        {"channel_name": extract_channel_name, "days": extract_days},
    ),
    (
        re.compile(r"([a-zA-Zа-яА-Я0-9_]+)\s+digest", re.IGNORECASE),
        IntentType.DATA_DIGEST,
        0.85,
        {"channel_name": extract_channel_name},
    ),
    # General digest request (no channel specified)
    (
        re.compile(r"(дайджест|digest|summary)\s*(?:за|for)?\s*(\d+)\s*(?:дн|days?|day)?", re.IGNORECASE),
        IntentType.DATA_DIGEST,
        0.90,
        {"days": extract_days},
    ),
    (
        re.compile(r"(дайджест|digest|последнее|latest)", re.IGNORECASE),
        IntentType.DATA_DIGEST,
        0.85,
        {},
    ),
    # Statistics patterns
    (
        re.compile(r"(статистика|stats|statistics)\s+(студент|student|ученик)", re.IGNORECASE),
        IntentType.DATA_STATS,
        0.90,
        {},
    ),
    # Homework status patterns (HIGH PRIORITY - should match before stats)
    # Most specific patterns first (highest confidence)
    (
        re.compile(r"(дай|покажи|пока|show|give me)\s+(?:мне\s+)?(?:полный\s+)?статус\s+(?:всех\s+)?(?:проверок\s+)?домашних\s+(?:заданий|работ|домашек|домашк)", re.IGNORECASE),
        IntentType.DATA_HW_STATUS,
        0.99,
        {},
    ),
    (
        re.compile(r"(дай|покажи|show|give me)\s+статус\s+проверки\s+домашних\s+заданий", re.IGNORECASE),
        IntentType.DATA_HW_STATUS,
        0.98,
        {},
    ),
    (
        re.compile(r"(статус\s+)?(?:всех\s+)?проверок\s+(?:домашних\s+)?(?:заданий|работ|домашек|домашк|homework|hw)", re.IGNORECASE),
        IntentType.DATA_HW_STATUS,
        0.97,
        {},
    ),
    (
        re.compile(r"(статус\s+)?проверки\s+(?:домашек|домашк|домашних\s+заданий|homework|hw)", re.IGNORECASE),
        IntentType.DATA_HW_STATUS,
        0.96,
        {},
    ),
    (
        re.compile(r"(покажи|show|дай|give me)\s+(?:статус\s+)?(?:проверки\s+)?(?:домашек|домашк|домашних\s+заданий|homework|hw)(?:\s+status)?", re.IGNORECASE),
        IntentType.DATA_HW_STATUS,
        0.95,
        {},
    ),
    (
        re.compile(r"(статус|status)\s+(?:проверки\s+)?(?:домашек|домашк|домашних\s+заданий|homework|hw)", re.IGNORECASE),
        IntentType.DATA_HW_STATUS,
        0.92,
        {},
    ),
    # Homework queue status patterns
    (
        re.compile(r"(покажи|show|дай|give me)\s+(?:статус\s+)?(?:очеред[ьи]|queue)(?:\s+status)?", re.IGNORECASE),
        IntentType.DATA_HW_QUEUE,
        0.95,
        {},
    ),
    (
        re.compile(r"(статус|status)\s+(?:очеред[ьи]|queue)", re.IGNORECASE),
        IntentType.DATA_HW_QUEUE,
        0.90,
        {},
    ),
    # Homework retry patterns
    (
        re.compile(r"(перезапусти|retry|restart|rerun)\s+(?:сабмит|submission)\s+([a-zA-Zа-яА-Я0-9_.-]+)", re.IGNORECASE),
        IntentType.DATA_HW_RETRY,
        0.95,
        {"submission_id": extract_submission_identifier},
    ),
    (
        re.compile(r"(перезапусти|retry|restart|rerun)\s+([a-zA-Zа-яА-Я0-9_.-]+)\s+(?:для|for|сабмит|submission)", re.IGNORECASE),
        IntentType.DATA_HW_RETRY,
        0.90,
        {"submission_id": extract_submission_identifier},
    ),
    (
        re.compile(r"(перезапусти|retry)\s+(?:сабмит|submission)(?:\s+(?:задания|assignment))?\s*(?:HW(\d+))?", re.IGNORECASE),
        IntentType.DATA_HW_RETRY,
        0.85,
        {"assignment": extract_assignment},
    ),
]

