"""Intent value object for God Agent."""

from dataclasses import dataclass
from enum import Enum


class IntentType(str, Enum):
    """Intent type enumeration.

    Purpose:
        Represents different types of user intents that God Agent can handle.

    Values:
        CONCIERGE: General conversation, greetings, personal assistance
        RESEARCH: Research questions requiring RAG/knowledge base lookup
        BUILD: Code generation and implementation tasks
        REVIEW: Code review and analysis tasks
        OPS: Operations, deployment, and infrastructure tasks
    """

    CONCIERGE = "concierge"
    RESEARCH = "research"
    BUILD = "build"
    REVIEW = "review"
    OPS = "ops"


@dataclass(frozen=True)
class Intent:
    """Intent value object.

    Purpose:
        Immutable value object representing user intent classification result
        with confidence score.

    Attributes:
        intent_type: Type of intent (concierge, research, build, review, ops).
        confidence: Confidence score in range [0.0, 1.0].

    Example:
        >>> intent = Intent(
        ...     intent_type=IntentType.RESEARCH,
        ...     confidence=0.85
        ... )
        >>> intent.intent_type
        <IntentType.RESEARCH: 'research'>
        >>> intent.confidence
        0.85
    """

    intent_type: IntentType
    confidence: float

    def __post_init__(self) -> None:
        """Validate Intent attributes."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
