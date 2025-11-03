"""Base intent classification types and protocols.

Following Python Zen:
- Explicit is better than implicit
- Simple is better than complex
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Protocol


class IntentType(Enum):
    """Intent type enumeration.

    Represents all possible user intents, including mode-level and sub-intents.
    """

    # Mode-level intents
    TASK = "task"
    DATA = "data"
    REMINDERS = "reminders"
    IDLE = "idle"

    # Sub-intents for better entity extraction
    TASK_CREATE = "task.create"
    TASK_LIST = "task.list"
    TASK_UPDATE = "task.update"
    TASK_DELETE = "task.delete"
    DATA_DIGEST = "data.digest"
    DATA_SUBSCRIPTION_LIST = "data.subscription.list"
    DATA_SUBSCRIPTION_ADD = "data.subscription.add"
    DATA_SUBSCRIPTION_REMOVE = "data.subscription.remove"
    DATA_STATS = "data.stats"
    DATA_HW_STATUS = "data.hw.status"
    DATA_HW_QUEUE = "data.hw.queue"
    DATA_HW_RETRY = "data.hw.retry"
    REMINDER_SET = "reminder.set"
    REMINDER_LIST = "reminder.list"
    REMINDER_DELETE = "reminder.delete"
    GENERAL_CHAT = "general.chat"
    GENERAL_QUESTION = "general.question"


@dataclass
class IntentResult:
    """Result of intent classification.

    Attributes:
        intent: Detected intent type
        confidence: Confidence score (0.0 to 1.0)
        source: Classification source ("rule", "llm", "cached")
        entities: Extracted entities (channel names, dates, etc.)
        latency_ms: Classification latency in milliseconds
    """

    intent: IntentType
    confidence: float
    source: str  # "rule", "llm", "cached"
    entities: Dict[str, any] = field(default_factory=dict)
    latency_ms: float = 0.0

    def __post_init__(self):
        """Validate intent result.

        Raises:
            ValueError: If confidence is out of bounds
        """
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


class IntentClassifierProtocol(Protocol):
    """Protocol for intent classifiers.

    All intent classifiers must implement this interface.
    """

    async def classify(self, message: str) -> IntentResult:
        """Classify user message intent.

        Args:
            message: User message text

        Returns:
            IntentResult with classified intent, confidence, and entities
        """
        ...

