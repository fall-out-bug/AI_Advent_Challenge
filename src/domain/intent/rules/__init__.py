"""Intent classification rule patterns.

Following Python Zen: Simple is better than complex.
"""

from src.domain.intent.rules.data_rules import DATA_RULES
from src.domain.intent.rules.general_rules import GENERAL_RULES
from src.domain.intent.rules.mode_rules import MODE_RULES
from src.domain.intent.rules.task_rules import TASK_RULES

__all__ = [
    "MODE_RULES",
    "TASK_RULES",
    "DATA_RULES",
    "GENERAL_RULES",
]

# Combine all rules: specific rules first (higher priority), then general mode rules
# This ensures sub-intents (TASK_CREATE) are matched before general intents (TASK)
ALL_RULES = TASK_RULES + DATA_RULES + MODE_RULES + GENERAL_RULES
