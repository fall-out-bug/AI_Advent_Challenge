"""Use case for generating task summaries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from src.application.dtos.digest_dtos import TaskSummaryResult
from src.infrastructure.database.mongo import get_db
from src.infrastructure.repositories.task_repository import TaskRepository


def _build_summary_query(user_id: int, timeframe: str, now: datetime) -> dict[str, Any]:
    """Build MongoDB query for task summary.

    Args:
        user_id: User ID.
        timeframe: Timeframe string (today/week/all).
        now: Current datetime.

    Returns:
        MongoDB query dictionary.
    """
    query: dict[str, Any] = {"user_id": user_id}

    if timeframe == "today":
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query["created_at"] = {"$gte": today_start}
    elif timeframe == "week":
        week_ago = now - timedelta(days=7)
        query["created_at"] = {"$gte": week_ago}

    return query


def _compute_task_stats(tasks: list[dict], now_iso: str) -> dict[str, Any]:
    """Compute task statistics.

    Args:
        tasks: List of task dictionaries.
        now_iso: Current datetime in ISO format.

    Returns:
        Statistics dictionary.
    """
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    pending = sum(1 for t in tasks if t.get("status") == "pending")
    high_priority = sum(1 for t in tasks if t.get("priority") == "high")
    with_deadline = sum(
        1
        for t in tasks
        if t.get("deadline")
        and datetime.fromisoformat(t["deadline"].replace("Z", "+00:00"))
        > datetime.now(timezone.utc)
    )

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "high_priority": high_priority,
        "with_deadline": with_deadline,
        "computed_at": now_iso,
    }


class GenerateTaskSummaryUseCase:
    """Use case for generating task summaries.

    Purpose:
        Fetches tasks for a user within a timeframe and computes statistics.
        No LLM summarization needed - this is just data aggregation.

    Args:
        task_repository: Optional TaskRepository (will create if not provided).
    """

    def __init__(self, task_repository: TaskRepository | None = None) -> None:
        self._task_repository = task_repository

    async def execute(
        self, user_id: int, timeframe: str = "today"
    ) -> TaskSummaryResult:
        """Execute task summary generation.

        Purpose:
            Queries tasks from database and computes statistics.

        Args:
            user_id: Telegram user ID.
            timeframe: Timeframe for filtering (today/week/all).

        Returns:
            TaskSummaryResult with tasks and statistics.
        """
        now = datetime.now(timezone.utc)

        # Get repository
        if self._task_repository is None:
            db = await get_db()
            repo = TaskRepository(db)
        else:
            repo = self._task_repository

        # Build query
        query = _build_summary_query(user_id=user_id, timeframe=timeframe, now=now)

        # Fetch tasks
        tasks_cursor = repo._collection.find(query).sort("created_at", -1)
        tasks_list = await tasks_cursor.to_list(length=1000)

        # Convert ObjectId to string for JSON serialization
        tasks = []
        for task in tasks_list:
            task_dict = dict(task)
            task_dict["_id"] = str(task_dict["_id"])
            # Convert datetime to ISO string
            for key in ["created_at", "deadline", "updated_at"]:
                if key in task_dict and isinstance(task_dict[key], datetime):
                    task_dict[key] = task_dict[key].isoformat()
            tasks.append(task_dict)

        # Compute stats
        stats = _compute_task_stats(tasks, now.isoformat())

        return TaskSummaryResult(
            tasks=tasks,
            stats=stats,
            timeframe=timeframe,
            generated_at=now,
        )
