"""Value object for long summarization tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.task_status import TaskStatus


@dataclass
class LongSummarizationTask:
    """Long-running summarization task.

    Purpose:
        Represents an asynchronous summarization task that will be
        processed by a background worker with extended timeout.
        Used for large digests that may take several minutes.

    Args:
        task_id: Unique task identifier
        user_id: Telegram user ID
        chat_id: Telegram chat ID for sending results
        channel_username: Channel username to summarize (optional)
        context: Summarization context (time period, language, etc.)
        status: Current task status
        result_text: Generated summary text (if succeeded)
        error: Error message (if failed)
        created_at: Task creation timestamp
        started_at: Task start timestamp (if running/succeeded/failed)
        finished_at: Task completion timestamp (if succeeded/failed)
    """

    task_id: str
    user_id: int
    chat_id: int
    channel_username: str | None = None
    context: SummarizationContext = field(default_factory=SummarizationContext)
    status: TaskStatus = TaskStatus.QUEUED
    result_text: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate task data."""
        if not self.task_id:
            raise ValueError("task_id cannot be empty")
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        if self.chat_id <= 0:
            raise ValueError("chat_id must be positive")
        if self.status not in TaskStatus:
            raise ValueError(f"Invalid status: {self.status}")

    def mark_running(self) -> None:
        """Mark task as running."""
        if self.status != TaskStatus.QUEUED:
            raise ValueError(f"Cannot mark as running from status: {self.status}")
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_succeeded(self, result_text: str) -> None:
        """Mark task as succeeded with result.

        Args:
            result_text: Generated summary text
        """
        if self.status != TaskStatus.RUNNING:
            raise ValueError(f"Cannot mark as succeeded from status: {self.status}")
        self.status = TaskStatus.SUCCEEDED
        self.result_text = result_text
        self.finished_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error.

        Args:
            error: Error message
        """
        if self.status not in (TaskStatus.QUEUED, TaskStatus.RUNNING):
            raise ValueError(f"Cannot mark as failed from status: {self.status}")
        self.status = TaskStatus.FAILED
        self.error = error
        if not self.started_at:
            self.started_at = datetime.utcnow()
        self.finished_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary for storage.

        Returns:
            Dictionary representation of task
        """
        return {
            "_id": self.task_id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "channel_username": self.channel_username,
            "context": {
                "time_period_hours": self.context.time_period_hours,
                "source_type": self.context.source_type,
                "max_chars": self.context.max_chars,
                "language": self.context.language,
                "max_sentences": self.context.max_sentences,
                "user_preferences": self.context.user_preferences,
                "additional_metadata": self.context.additional_metadata,
            },
            "status": self.status.value,
            "result_text": self.result_text,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LongSummarizationTask:
        """Create task from dictionary.

        Args:
            data: Dictionary representation of task

        Returns:
            LongSummarizationTask instance
        """
        context_data = data.get("context", {})
        context = SummarizationContext(
            time_period_hours=context_data.get("time_period_hours"),
            source_type=context_data.get("source_type", "telegram_posts"),
            max_chars=context_data.get("max_chars"),
            language=context_data.get("language", "ru"),
            max_sentences=context_data.get("max_sentences"),
            user_preferences=context_data.get("user_preferences", {}),
            additional_metadata=context_data.get("additional_metadata", {}),
        )

        return cls(
            task_id=data["task_id"],
            user_id=data["user_id"],
            chat_id=data["chat_id"],
            channel_username=data.get("channel_username"),
            context=context,
            status=TaskStatus(data.get("status", TaskStatus.QUEUED.value)),
            result_text=data.get("result_text"),
            error=data.get("error"),
            created_at=data.get("created_at", datetime.utcnow()),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
        )

