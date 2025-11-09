"""Reminder intent classification rules.

Patterns for reminder creation, listing, and deletion.
Following Python Zen: Simple is better than complex.
"""

import re
from typing import Callable, Dict, Tuple

from src.domain.intent.intent_classifier import IntentType


def extract_reminder_text(match: re.Match) -> str:
    """Extract reminder text from match.

    Args:
        match: Regex match object

    Returns:
        Reminder text or empty string
    """
    if match.lastindex >= 1:
        return match.group(1).strip()
    return ""


REMINDER_RULES: list[Tuple[re.Pattern, IntentType, float, Dict[str, Callable]]] = [
    # Reminder creation patterns
    (
        re.compile(r"напомни\s+мне\s+(?:про|about|о)?\s*(.+?)", re.IGNORECASE),
        IntentType.REMINDER_SET,
        0.95,
        {"reminder_text": extract_reminder_text},
    ),
    (
        re.compile(r"remind\s+me\s+(?:about|of|to)?\s*(.+?)", re.IGNORECASE),
        IntentType.REMINDER_SET,
        0.95,
        {"reminder_text": extract_reminder_text},
    ),
    (
        re.compile(r"напоминани\s+(?:о|про|about)?\s*(.+?)", re.IGNORECASE),
        IntentType.REMINDER_SET,
        0.85,
        {"reminder_text": extract_reminder_text},
    ),
    # Reminder listing patterns
    (
        re.compile(r"(когда|when|какие|what)\s+(напоминани|reminder)", re.IGNORECASE),
        IntentType.REMINDER_LIST,
        0.90,
        {},
    ),
    (
        re.compile(r"(мои|my)\s+(напоминани|reminder)", re.IGNORECASE),
        IntentType.REMINDER_LIST,
        0.95,
        {},
    ),
    (
        re.compile(r"(ближайшие|upcoming|next)\s+(напоминани|reminder)", re.IGNORECASE),
        IntentType.REMINDER_LIST,
        0.90,
        {},
    ),
    # Reminder deletion patterns
    (
        re.compile(
            r"(удали|delete|remove|убери)\s+(напоминани|reminder)", re.IGNORECASE
        ),
        IntentType.REMINDER_DELETE,
        0.95,
        {},
    ),
]
