"""Value object for long-running tasks (summarization and code review)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.task_status import TaskStatus
from src.domain.value_objects.task_type import TaskType


@dataclass
class LongTask:
    """Long-running task (unified for summarization and code review).

    Purpose:
        Represents an asynchronous task that will be processed by a
        background worker. Supports multiple task types through the
        task_type field and metadata for type-specific data.

    Args:
        task_id: Unique task identifier
        task_type: Type of task (SUMMARIZATION or CODE_REVIEW)
        user_id: Telegram user ID (for summarization) or student ID (for review)
        chat_id: Telegram chat ID for sending results (for summarization)
        channel_username: Channel username to summarize (optional, summarization only)
        context: Summarization context (time period, language, etc., summarization only)
        status: Current task status
        result_text: Generated summary text or session_id (if succeeded)
        error: Error message (if failed)
        created_at: Task creation timestamp
        started_at: Task start timestamp (if running/succeeded/failed)
        finished_at: Task completion timestamp (if succeeded/failed)
        metadata: Additional type-specific data (e.g., review task paths, assignment_id)
    """

    task_id: str
    task_type: TaskType
    user_id: int
    chat_id: int | None = None  # Optional for code review tasks
    channel_username: str | None = None
    context: SummarizationContext | None = field(default=None)
    status: TaskStatus = TaskStatus.QUEUED
    result_text: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate task data."""
        if not self.task_id:
            raise ValueError("task_id cannot be empty")
        if self.user_id <= 0:
            raise ValueError("user_id must be positive")
        if self.task_type == TaskType.SUMMARIZATION and self.chat_id is None:
            raise ValueError("chat_id is required for SUMMARIZATION tasks")
        # chat_id can be None for CODE_REVIEW tasks (user_id is student_id, not chat_id)
        if self.status not in TaskStatus:
            raise ValueError(f"Invalid status: {self.status}")
        if self.task_type not in TaskType:
            raise ValueError(f"Invalid task_type: {self.task_type}")

    def mark_running(self) -> None:
        """Mark task as running."""
        if self.status != TaskStatus.QUEUED:
            raise ValueError(f"Cannot mark as running from status: {self.status}")
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_succeeded(self, result_text: str) -> None:
        """Mark task as succeeded with result.

        Args:
            result_text: Generated summary text or session_id
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
        result: dict[str, Any] = {
            "_id": self.task_id,
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "channel_username": self.channel_username,
            "status": self.status.value,
            "result_text": self.result_text,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "metadata": self.metadata,
        }

        # Add context only for summarization tasks (backward compatibility)
        if self.task_type == TaskType.SUMMARIZATION and self.context:
            result["context"] = {
                "time_period_hours": self.context.time_period_hours,
                "source_type": self.context.source_type,
                "max_chars": self.context.max_chars,
                "language": self.context.language,
                "max_sentences": self.context.max_sentences,
                "user_preferences": self.context.user_preferences,
                "additional_metadata": self.context.additional_metadata,
            }

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LongTask":
        """Create task from dictionary.

        Args:
            data: Dictionary representation of task

        Returns:
            LongTask instance
        """
        task_type = TaskType(data.get("task_type", TaskType.SUMMARIZATION.value))

        # Parse context only for summarization tasks
        context = None
        if task_type == TaskType.SUMMARIZATION and "context" in data:
            context_data = data.get("context", {})
            from src.domain.value_objects.summarization_context import (
                SummarizationContext,
            )

            context = SummarizationContext(
                time_period_hours=context_data.get("time_period_hours"),
                source_type=context_data.get("source_type", "telegram_posts"),
                max_chars=context_data.get("max_chars"),
                language=context_data.get("language", "ru"),
                max_sentences=context_data.get("max_sentences"),
                user_preferences=context_data.get("user_preferences", {}),
                additional_metadata=context_data.get("additional_metadata", {}),
            )

        # Ensure user_id is int (it should already be int from EnqueueReviewTaskUseCase)
        user_id = data.get("user_id")
        if isinstance(user_id, str):
            # Fallback: convert string to int (shouldn't happen in normal flow)
            try:
                user_id = int(user_id)
            except ValueError:
                # If conversion fails, use hash as fallback
                user_id = abs(hash(user_id)) % (10**9)
        elif user_id is None:
            raise ValueError("user_id is required")
        
        task = cls(
            task_id=data["task_id"],
            task_type=task_type,
            user_id=int(user_id),
            chat_id=data.get("chat_id"),
            channel_username=data.get("channel_username"),
            context=context,
            status=TaskStatus(data.get("status", TaskStatus.QUEUED.value)),
            result_text=data.get("result_text"),
            error=data.get("error"),
            created_at=data.get("created_at", datetime.utcnow()),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            metadata=data.get("metadata", {}),
        )
        return task


# Backward compatibility alias
LongSummarizationTask = LongTask

