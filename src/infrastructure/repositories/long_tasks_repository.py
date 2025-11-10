"""Repository for long-running tasks (summarization and code review) with idempotent operations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from src.domain.value_objects.long_summarization_task import LongTask
from src.domain.value_objects.task_status import TaskStatus
from src.domain.value_objects.task_type import TaskType
from src.infrastructure.logging import get_logger

logger = get_logger("long_tasks_repository")


class LongTasksRepository:
    """Async repository for long-running tasks (summarization and code review).

    Purpose:
        Encapsulate CRUD operations for long-running tasks of all types.
        Provides idempotent operations to prevent double-processing.
        Uses MongoDB for persistence with atomic updates.
        Supports filtering by task type for unified worker processing.

    Exceptions:
        ValueError: If provided inputs are invalid
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize repository."""
        self._db = db
        self._indexes_created = False

    async def _ensure_indexes(self) -> None:
        """Create required indexes for efficient queries."""
        if self._indexes_created:
            return

        collection = self._db.long_tasks
        await collection.create_index(
            [("task_type", 1), ("status", 1), ("created_at", 1)]
        )
        await collection.create_index([("status", 1), ("created_at", 1)])
        await collection.create_index([("user_id", 1), ("created_at", -1)])
        await collection.create_index(
            [("metadata.assignment_id", 1), ("created_at", -1)]
        )
        await collection.create_index([("task_id", 1)], unique=True)
        await collection.create_index(
            [("created_at", 1)], expireAfterSeconds=604800
        )  # 7 days TTL
        self._indexes_created = True

    async def create(self, task: LongTask) -> str:
        """Create new task."""
        await self._ensure_indexes()

        collection = self._db.long_tasks
        task_dict = task.to_dict()

        try:
            await collection.insert_one(task_dict)
            logger.info(
                "Created long task: task_id=%s, type=%s, user_id=%s",
                task.task_id,
                task.task_type.value,
                task.user_id,
            )
            return task.task_id
        except Exception as exc:  # pragma: no cover - defensive
            if "duplicate key" in str(exc).lower() or "E11000" in str(exc):
                logger.warning(
                    "Task already exists (idempotent): task_id=%s, type=%s, user_id=%s",
                    task.task_id,
                    task.task_type.value,
                    task.user_id,
                )
                return task.task_id
            raise

    async def pick_next_queued(
        self, task_type: TaskType | None = None
    ) -> LongTask | None:
        """Pick next queued task for processing."""
        await self._ensure_indexes()

        collection = self._db.long_tasks
        query: dict[str, Any] = {"status": TaskStatus.QUEUED.value}
        if task_type:
            query["task_type"] = task_type.value

        result = await collection.find_one_and_update(
            query,
            {
                "$set": {
                    "status": TaskStatus.RUNNING.value,
                    "started_at": datetime.utcnow(),
                }
            },
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )

        if not result:
            return None

        try:
            task = LongTask.from_dict(result)
            logger.info(
                "Picked queued task: task_id=%s, type=%s, user_id=%s",
                task.task_id,
                task.task_type.value,
                task.user_id,
            )
            return task
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                "Failed to deserialize task: task_id=%s, error=%s",
                result.get("task_id"),
                exc,
                exc_info=True,
            )
            await collection.update_one(
                {"task_id": result.get("task_id")},
                {
                    "$set": {
                        "status": TaskStatus.FAILED.value,
                        "error": f"Deserialization error: {exc}",
                        "finished_at": datetime.utcnow(),
                    }
                },
            )
            return None

    async def mark_running(self, task_id: str) -> None:
        """Mark task as running (idempotent)."""
        await self._ensure_indexes()

        collection = self._db.long_tasks
        result = await collection.update_one(
            {"task_id": task_id, "status": TaskStatus.QUEUED.value},
            {
                "$set": {
                    "status": TaskStatus.RUNNING.value,
                    "started_at": datetime.utcnow(),
                }
            },
        )

        if result.modified_count > 0:
            logger.info("Marked task as running: task_id=%s", task_id)
        else:
            logger.debug("Task already running or not queued: task_id=%s", task_id)

    async def complete(self, task_id: str, result_text: str) -> None:
        """Mark task as succeeded with result."""
        await self._ensure_indexes()

        collection = self._db.long_tasks
        await collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.SUCCEEDED.value,
                    "result_text": result_text,
                    "finished_at": datetime.utcnow(),
                }
            },
        )

    async def fail(self, task_id: str, error: str) -> None:
        """Mark task as failed with error."""
        await self._ensure_indexes()

        collection = self._db.long_tasks
        await collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.FAILED.value,
                    "error": error[:1000],
                    "finished_at": datetime.utcnow(),
                }
            },
        )

    async def get_by_id(self, task_id: str) -> LongTask | None:
        """Get task by ID."""
        await self._ensure_indexes()

        collection = self._db.long_tasks
        result = await collection.find_one({"task_id": task_id})
        if not result:
            return None

        try:
            return LongTask.from_dict(result)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                "Failed to deserialize task: task_id=%s, error=%s",
                task_id,
                exc,
                exc_info=True,
            )
            return None

    async def get_by_user(
        self,
        user_id: int,
        limit: int = 10,
        status: TaskStatus | None = None,
        task_type: TaskType | None = None,
    ) -> list[LongTask]:
        """Get tasks by user ID."""
        await self._ensure_indexes()

        collection = self._db.long_tasks
        query: dict[str, Any] = {"user_id": user_id}
        if status:
            query["status"] = status.value
        if task_type:
            query["task_type"] = task_type.value

        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        tasks: list[LongTask] = []

        async for doc in cursor:
            try:
                task = LongTask.from_dict(doc)
                tasks.append(task)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to deserialize task: error=%s", exc, exc_info=True)

        return tasks

    async def get_queue_size(self, task_type: TaskType | None = None) -> int:
        """Get number of queued tasks."""
        await self._ensure_indexes()
        collection = self._db.long_tasks
        query: dict[str, Any] = {"status": TaskStatus.QUEUED.value}
        if task_type:
            query["task_type"] = task_type.value
        return await collection.count_documents(query)

    async def count_reviews_in_window(
        self,
        *,
        user_id: int | None = None,
        assignment_id: str | None = None,
        window_seconds: int,
    ) -> int:
        """Count review tasks created within the specified time window."""
        await self._ensure_indexes()

        collection = self._db.long_tasks
        threshold = datetime.utcnow() - timedelta(seconds=window_seconds)
        query: dict[str, Any] = {
            "task_type": TaskType.CODE_REVIEW.value,
            "created_at": {"$gte": threshold},
        }
        if user_id is not None:
            query["user_id"] = user_id
        if assignment_id is not None:
            query["metadata.assignment_id"] = assignment_id

        return await collection.count_documents(query)
