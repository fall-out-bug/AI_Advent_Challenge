"""Task intent classification rules.

Patterns for task creation, listing, updating, and deletion.
Following Python Zen: Simple is better than complex.
"""

import re
from typing import Callable, Dict, Tuple

from src.domain.intent.intent_classifier import IntentType


def extract_task_title(match: re.Match) -> str:
    """Extract task title from match.

    Args:
        match: Regex match object

    Returns:
        Task title or empty string
    """
    return match.group(1) if match.lastindex >= 1 else ""


TASK_RULES: list[Tuple[re.Pattern, IntentType, float, Dict[str, Callable]]] = [
    # Task creation patterns
    (
        re.compile(r"(создай|добавь|create|add)\s+(задачу|задач|task)\s+(?:на|to|для|for)?\s*(.+)?", re.IGNORECASE),
        IntentType.TASK_CREATE,
        0.95,
        {"title": extract_task_title},
    ),
    (
        re.compile(r"(нужно|надо|need|must)\s+(.+?)(?:сделать|do|выполнить|execute)", re.IGNORECASE),
        IntentType.TASK_CREATE,
        0.85,
        {"title": extract_task_title},
    ),
    (
        re.compile(r"(запомни|сохрани|remember|save)\s+(.+?)", re.IGNORECASE),
        IntentType.TASK_CREATE,
        0.90,
        {"title": extract_task_title},
    ),
    # Task listing patterns
    (
        re.compile(r"(какие|мои|show|list|покажи)\s+(задач|task|дел|todos)", re.IGNORECASE),
        IntentType.TASK_LIST,
        0.95,
        {},
    ),
    (
        re.compile(r"что\s+(мне|нужно|надо)\s+(делать|сделать)", re.IGNORECASE),
        IntentType.TASK_LIST,
        0.85,
        {},
    ),
    # Task update patterns
    (
        re.compile(r"(измени|update|change|изменя|редактир|edit)\s+(задачу|task)", re.IGNORECASE),
        IntentType.TASK_UPDATE,
        0.90,
        {},
    ),
    # Task deletion patterns
    (
        re.compile(r"(удали|delete|remove|убери)\s+(задачу|task)", re.IGNORECASE),
        IntentType.TASK_DELETE,
        0.95,
        {},
    ),
]

