"""DTOs for digest and summary use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.summary_result import SummaryResult


@dataclass
class ChannelDigest:
    """Channel digest data transfer object.

    Args:
        channel_username: Channel username without @.
        channel_title: Optional channel title.
        summary: SummaryResult from summarization.
        post_count: Number of posts summarized.
        time_window_hours: Time window in hours.
        tags: Optional tags/metadata.
        generated_at: Generation timestamp.
    """

    channel_username: str
    channel_title: str | None
    summary: SummaryResult
    post_count: int
    time_window_hours: int
    tags: list[str]
    generated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "channel": self.channel_username,
            "channel_title": self.channel_title,
            "summary": self.summary.text,
            "post_count": self.post_count,
            "hours": self.time_window_hours,
            "tags": self.tags,
            "generated_at": self.generated_at.isoformat(),
            "sentences_count": self.summary.sentences_count,
            "method": self.summary.method,
            "confidence": self.summary.confidence,
        }


@dataclass
class TaskSummaryResult:
    """Task summary result DTO.

    Args:
        tasks: List of task dictionaries.
        stats: Task statistics dictionary.
        timeframe: Timeframe string (today/week/all).
        generated_at: Generation timestamp.
    """

    tasks: list[dict]
    stats: dict
    timeframe: str
    generated_at: datetime

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "tasks": self.tasks,
            "stats": self.stats,
            "timeframe": self.timeframe,
            "generated_at": self.generated_at.isoformat(),
        }
