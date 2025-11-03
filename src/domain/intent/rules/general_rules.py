"""General intent classification rules.

Fallback patterns for greetings, chat, and unclear intents.
Following Python Zen: Simple is better than complex.
"""

import re
from typing import Callable, Dict, Tuple

from src.domain.intent.intent_classifier import IntentType

GENERAL_RULES: list[Tuple[re.Pattern, IntentType, float, Dict[str, Callable]]] = [
    # Greeting patterns
    (
        re.compile(r"^(привет|hello|hi|здравствуй|hey|добр)", re.IGNORECASE),
        IntentType.GENERAL_CHAT,
        0.85,
        {},
    ),
    (
        re.compile(r"(как дела|how are you|how's it going)", re.IGNORECASE),
        IntentType.GENERAL_CHAT,
        0.80,
        {},
    ),
    (
        re.compile(r"(что нового|what's new|что случилось|what happened)", re.IGNORECASE),
        IntentType.GENERAL_CHAT,
        0.75,
        {},
    ),
    # Question patterns
    (
        re.compile(r"(какая|what|which)\s+(погода|weather)", re.IGNORECASE),
        IntentType.GENERAL_QUESTION,
        0.85,
        {},
    ),
    (
        re.compile(r"(сколько|how much|how many)\s+", re.IGNORECASE),
        IntentType.GENERAL_QUESTION,
        0.80,
        {},
    ),
    (
        re.compile(r"^(что|what|where|when|why|who|как|how)\s+", re.IGNORECASE),
        IntentType.GENERAL_QUESTION,
        0.75,
        {},
    ),
]

