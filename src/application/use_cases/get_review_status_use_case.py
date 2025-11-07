"""Use case for getting review task status."""

from __future__ import annotations

from typing import Any

from src.infrastructure.repositories.homework_review_repository import (
    HomeworkReviewRepository,
)
from src.infrastructure.repositories.long_tasks_repository import LongTasksRepository


class GetReviewStatusUseCase:
    """Use case for retrieving review task status.

    Purpose:
        Gets task status from LongTasksRepository and review results
        from HomeworkReviewRepository if available.

    Args:
        tasks_repository: LongTasksRepository instance
        review_repository: HomeworkReviewRepository instance
    """

    def __init__(
        self,
        tasks_repository: LongTasksRepository,
        review_repository: HomeworkReviewRepository,
    ) -> None:
        """Initialize use case.

        Args:
            tasks_repository: Tasks repository
            review_repository: Review repository
        """
        self.tasks_repository = tasks_repository
        self.review_repository = review_repository

    async def execute(self, task_id: str) -> dict[str, Any]:
        """Get review task status.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with task status and result
        """
        task = await self.tasks_repository.get_by_id(task_id)

        if not task:
            return {"status": "not_found"}

        result: dict[str, Any] = {
            "task_id": task.task_id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None,
            "error": task.error,
        }

        # Add metadata fields for API response
        metadata = task.metadata
        result["student_id"] = metadata.get("student_id")
        result["assignment_id"] = metadata.get("assignment_id")

        # If task succeeded, try to get review session
        if task.status.value == "succeeded" and task.result_text:
            session_id = task.result_text
            review_session = await self.review_repository.get_review_session(session_id)
            if review_session:
                result["result"] = {
                    "session_id": session_id,
                    "report": review_session.get("report", {}),
                }

        return result

