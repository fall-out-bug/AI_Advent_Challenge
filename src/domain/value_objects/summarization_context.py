"""Value objects for summarization context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SummarizationContext:
    """Context for summarization operations.

    Purpose:
        Provides contextual information to guide summarization,
        such as time period, source type, and user preferences.

    Args:
        time_period_hours: Time period in hours for temporal context.
        source_type: Type of source ("telegram_posts" | "tasks" | "documents").
        max_chars: Maximum characters for summary (soft limit, not hard truncation).
        language: Language for summary ("ru" | "en").
        max_sentences: Maximum number of sentences (soft limit).
        user_preferences: User-specific preferences.
        additional_metadata: Additional contextual metadata.
    """

    time_period_hours: int | None = None
    source_type: str = "telegram_posts"
    max_chars: int | None = None
    language: str = "ru"
    max_sentences: int | None = None
    user_preferences: dict[str, Any] = field(default_factory=dict)
    additional_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate context data."""
        valid_source_types = ("telegram_posts", "tasks", "documents", "general")
        if self.source_type not in valid_source_types:
            raise ValueError(
                f"Invalid source_type: {self.source_type}. "
                f"Must be one of {valid_source_types}"
            )
        if self.time_period_hours is not None and self.time_period_hours < 0:
            raise ValueError("time_period_hours cannot be negative")
