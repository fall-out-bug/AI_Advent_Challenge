"""Memory slice value object."""

from dataclasses import dataclass
from typing import List, Optional

from src.domain.personalization.user_memory_event import UserMemoryEvent


@dataclass
class MemorySlice:
    """Slice of user memory for prompt context.

    Purpose:
        Bundles recent events with optional summary for LLM prompts.
        Provides formatting method to convert events to prompt text.

    Attributes:
        events: List of recent memory events (chronological order).
        summary: Optional compressed summary of older interactions.
        total_events: Total number of events in full memory (for metrics).

    Example:
        >>> events = [UserMemoryEvent.create_user_event("123", "Hi")]
        >>> slice = MemorySlice(events=events, summary="Previous chat")
        >>> context = slice.to_prompt_context()
        >>> "Recent interactions" in context
        True
    """

    events: List[UserMemoryEvent]
    summary: Optional[str] = None
    total_events: int = 0

    def to_prompt_context(self, max_events: int = 10) -> str:
        """Format memory slice as LLM prompt context.

        Purpose:
            Convert events and summary into formatted text for injection
            into personalized prompts.

        Args:
            max_events: Maximum events to include (default: 10).

        Returns:
            Formatted context string with summary and recent events.

        Example:
            >>> slice = MemorySlice(events=[...], summary="User likes Python")
            >>> context = slice.to_prompt_context(max_events=5)
            >>> "Summary: User likes Python" in context
            True
        """
        lines = []

        # Add summary if available
        if self.summary:
            lines.append(f"Summary: {self.summary}\n")

        # Add recent events
        if self.events:
            lines.append("Recent interactions:")
            # Take last N events
            recent_events = self.events[-max_events:]
            for event in recent_events:
                role_label = "User" if event.role == "user" else "Butler"
                # Truncate long messages
                content_preview = event.content[:200]
                if len(event.content) > 200:
                    content_preview += "..."
                lines.append(f"- {role_label}: {content_preview}")

        return "\n".join(lines) if lines else ""
