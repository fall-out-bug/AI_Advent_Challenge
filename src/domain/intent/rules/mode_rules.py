"""Mode-level intent classification rules.

Patterns for identifying TASK, DATA, REMINDERS, IDLE modes.
Following Python Zen: Simple is better than complex.
"""

import re
from typing import Callable, Dict, Tuple

from src.domain.intent.intent_classifier import IntentType

# Rule format: (pattern, intent_type, confidence, entity_extractors)
# entity_extractors: Dict[str, Callable[[re.Match], any]]
MODE_RULES: list[Tuple[re.Pattern, IntentType, float, Dict[str, Callable]]] = [
    # TASK mode patterns
    (
        re.compile(r"(создай|добавь|напоминаю|create|add)\s+(задач|task|дело|todo)", re.IGNORECASE),
        IntentType.TASK,
        0.95,
        {},
    ),
    (
        re.compile(r"(нужно|надо|need|must)\s+.+(сделать|do|выполнить)", re.IGNORECASE),
        IntentType.TASK,
        0.85,
        {},
    ),
    (
        re.compile(r"(запомни|сохрани|remember|save)\s+.+", re.IGNORECASE),
        IntentType.TASK,
        0.90,
        {},
    ),
    (
        re.compile(r"(какие|мои|show|list|покажи)\s+(задач|task|дел|todos)", re.IGNORECASE),
        IntentType.TASK,
        0.95,
        {},
    ),
    # DATA mode patterns
    (
        re.compile(
            r"(мои|my|all my|все мои|give me|дай|покажи|show|list)\s+(подписк|subscription|канал|channels)",
            re.IGNORECASE,
        ),
        IntentType.DATA,
        0.95,
        {},
    ),
    (
        re.compile(
            r"(дайджест|digest|summary|последнее|latest)\s+(канал|channel|по|of|for)", re.IGNORECASE
        ),
        IntentType.DATA,
        0.95,
        {},
    ),
    (
        re.compile(r"(статистика|stats|statistics)\s+(студент|student|ученик)", re.IGNORECASE),
        IntentType.DATA,
        0.90,
        {},
    ),
    (
        re.compile(r"(подпиш|subscribe|добав|add)\s+(канал|channel)", re.IGNORECASE),
        IntentType.DATA,
        0.95,
        {},
    ),
    (
        re.compile(r"(отпис|unsubscribe|удал|remove|убери)\s+(канал|channel|от|from)", re.IGNORECASE),
        IntentType.DATA,
        0.95,
        {},
    ),
    # REMINDERS mode patterns
    (
        re.compile(r"(напомни|remind|напоминани|reminder)\s+(мне|me)", re.IGNORECASE),
        IntentType.REMINDERS,
        0.95,
        {},
    ),
    (
        re.compile(r"(когда|when|какие|what)\s+(напоминани|reminder)", re.IGNORECASE),
        IntentType.REMINDERS,
        0.90,
        {},
    ),
    # IDLE mode patterns (greetings, general chat)
    (
        re.compile(r"^(привет|hello|hi|здравствуй|hey|добр)", re.IGNORECASE),
        IntentType.IDLE,
        0.85,
        {},
    ),
    (
        re.compile(r"(как дела|how are you|что нового|what's new)", re.IGNORECASE),
        IntentType.IDLE,
        0.80,
        {},
    ),
]

