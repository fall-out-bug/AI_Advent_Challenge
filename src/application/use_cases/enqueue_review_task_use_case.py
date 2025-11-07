"""Use case for enqueueing code review tasks."""

from __future__ import annotations

import uuid
from datetime import datetime

from src.domain.value_objects.long_summarization_task import LongTask
from src.domain.value_objects.task_status import TaskStatus
from src.domain.value_objects.task_type import TaskType
from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository


class EnqueueReviewTaskUseCase:
    """Use case for creating and enqueueing code review tasks.

    Purpose:
        Validates input and creates a new code review task in the queue
        using LongTasksRepository with task_type=CODE_REVIEW.

    Args:
        repository: LongTasksRepository instance
    """

    def __init__(self, repository: LongTasksRepository) -> None:
        """Initialize use case.

        Args:
            repository: Long tasks repository
        """
        self.repository = repository

    async def execute(
        self,
        student_id: str,
        assignment_id: str,
        new_submission_path: str,
        new_commit: str,
        previous_submission_path: str | None = None,
        old_commit: str | None = None,
        logs_zip_path: str | None = None,
    ) -> LongTask:
        """Enqueue a new review task.

        Args:
            student_id: Student identifier (will be converted to int for user_id)
            assignment_id: Assignment identifier
            new_submission_path: Path to new submission ZIP
            previous_submission_path: Optional path to previous submission
            new_commit: Commit hash for new submission (required, non-empty)
            old_commit: Optional commit hash for previous submission
            logs_zip_path: Optional path to logs ZIP archive

        Returns:
            Created LongTask

        Raises:
            ValueError: If input validation fails
        """
        # Convert student_id to int (user_id field)
        try:
            user_id = int(student_id)
        except ValueError:
            raise ValueError(f"student_id must be numeric, got: {student_id}")

        normalized_new_commit = new_commit.strip()
        if not normalized_new_commit:
            raise ValueError("new_commit cannot be empty")

        task_id = f"rev_{uuid.uuid4().hex[:12]}"
        metadata = {
            "student_id": student_id,
            "assignment_id": assignment_id,
            "new_submission_path": new_submission_path,
            "previous_submission_path": previous_submission_path,
            "new_commit": normalized_new_commit,
        }
        if old_commit:
            metadata["old_commit"] = old_commit
        if logs_zip_path:
            metadata["logs_zip_path"] = logs_zip_path

        task = LongTask(
            task_id=task_id,
            task_type=TaskType.CODE_REVIEW,
            user_id=user_id,
            chat_id=None,  # Not needed for review tasks
            status=TaskStatus.QUEUED,
            created_at=datetime.utcnow(),
            metadata=metadata,
        )

        await self.repository.create(task)
        return task

