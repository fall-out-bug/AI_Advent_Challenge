"""User memory event value object."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class UserMemoryEvent:
    """Single interaction event in user memory.

    Purpose:
        Represents one message in conversation history (user or assistant).
        Events are stored chronologically and used to build context for LLM.

    Attributes:
        event_id: Unique event identifier (UUID).
        user_id: User this event belongs to.
        role: Message role ("user" or "assistant").
        content: Message text content.
        created_at: Event timestamp.
        tags: Optional tags for categorization.

    Example:
        >>> event = UserMemoryEvent.create_user_event("123", "Hello!")
        >>> event.role
        'user'
        >>> event.content
        'Hello!'
    """

    event_id: UUID
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate event data.

        Raises:
            ValueError: If required fields are invalid.
        """
        if not self.user_id:
            raise ValueError("user_id cannot be empty")

        if not self.content:
            raise ValueError("content cannot be empty")

        if self.role not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")

    @staticmethod
    def create_user_event(user_id: str, content: str) -> "UserMemoryEvent":
        """Create user message event.

        Args:
            user_id: User identifier.
            content: Message text.

        Returns:
            UserMemoryEvent with role="user".

        Example:
            >>> event = UserMemoryEvent.create_user_event("123", "Hello")
            >>> event.role
            'user'
        """
        return UserMemoryEvent(
            event_id=uuid4(),
            user_id=user_id,
            role="user",
            content=content,
            created_at=datetime.utcnow(),
            tags=[],
        )

    @staticmethod
    def create_assistant_event(user_id: str, content: str) -> "UserMemoryEvent":
        """Create assistant reply event.

        Args:
            user_id: User identifier.
            content: Reply text.

        Returns:
            UserMemoryEvent with role="assistant".

        Example:
            >>> event = UserMemoryEvent.create_assistant_event("123", "Hi!")
            >>> event.role
            'assistant'
        """
        return UserMemoryEvent(
            event_id=uuid4(),
            user_id=user_id,
            role="assistant",
            content=content,
            created_at=datetime.utcnow(),
            tags=[],
        )
