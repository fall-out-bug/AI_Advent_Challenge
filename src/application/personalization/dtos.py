"""DTOs for personalization use cases."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PersonalizedReplyInput:
    """Input DTO for personalized reply use case.

    Purpose:
        Encapsulates input data for generating personalized replies.

    Attributes:
        user_id: User identifier (Telegram user ID).
        text: User message text to respond to.
        source: Message source ("text" or "voice").

    Example:
        >>> input_data = PersonalizedReplyInput(
        ...     user_id="123",
        ...     text="Hello",
        ...     source="text"
        ... )
    """

    user_id: str
    text: str
    source: Literal["text", "voice"] = "text"


@dataclass(frozen=True)
class PersonalizedReplyOutput:
    """Output DTO for personalized reply use case.

    Purpose:
        Encapsulates result of personalized reply generation.

    Attributes:
        reply: Generated reply text from LLM.
        used_persona: Whether personalization was applied.
        memory_events_used: Number of memory events used for context.
        compressed: Whether memory was compressed during this request.

    Example:
        >>> output = PersonalizedReplyOutput(
        ...     reply="Good day, sir",
        ...     used_persona=True,
        ...     memory_events_used=10,
        ...     compressed=False
        ... )
    """

    reply: str
    used_persona: bool
    memory_events_used: int
    compressed: bool = False


@dataclass(frozen=True)
class ResetPersonalizationInput:
    """Input DTO for reset personalization use case.

    Purpose:
        Encapsulates input for resetting user profile and memory.

    Attributes:
        user_id: User identifier.

    Example:
        >>> input_data = ResetPersonalizationInput(user_id="123")
    """

    user_id: str


@dataclass(frozen=True)
class ResetPersonalizationOutput:
    """Output DTO for reset personalization use case.

    Purpose:
        Encapsulates result of reset operation.

    Attributes:
        success: Whether reset was successful.
        profile_reset: Whether profile was reset.
        memory_deleted_count: Number of memory events deleted.

    Example:
        >>> output = ResetPersonalizationOutput(
        ...     success=True,
        ...     profile_reset=True,
        ...     memory_deleted_count=50
        ... )
    """

    success: bool
    profile_reset: bool
    memory_deleted_count: int

