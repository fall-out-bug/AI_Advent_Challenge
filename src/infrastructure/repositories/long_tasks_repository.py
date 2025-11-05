"""Repository for long summarization tasks with idempotent operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from src.domain.value_objects.long_summarization_task import LongSummarizationTask
from src.domain.value_objects.task_status import TaskStatus
from src.infrastructure.logging import get_logger

logger = get_logger("long_tasks_repository")


class LongTasksRepository:
    """Async repository for long summarization tasks.

    Purpose:
        Encapsulate CRUD operations for long-running summarization tasks.
        Provides idempotent operations to prevent double-processing.
        Uses MongoDB for persistence with atomic updates.

    Exceptions:
        ValueError: If provided inputs are invalid
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize repository.

        Args:
            db: MongoDB database instance
        """
        self._db = db
        self._indexes_created = False

    async def _ensure_indexes(self) -> None:
        """Create required indexes for efficient queries."""
        if self._indexes_created:
            return

        collection = self._db.long_tasks
        await collection.create_index([("status", 1), ("created_at", 1)])
        await collection.create_index([("user_id", 1), ("created_at", -1)])
        await collection.create_index([("task_id", 1)], unique=True)
        await collection.create_index([("created_at", 1)], expireAfterSeconds=604800)  # 7 days TTL
        self._indexes_created = True

    async def create(self, task: LongSummarizationTask) -> str:
        """Create new task.

        Purpose:
            Persist task to database with idempotency check.
            If task with same task_id exists, returns existing task_id.

        Args:
            task: LongSummarizationTask to create

        Returns:
            Task ID

        Raises:
            ValueError: If task data is invalid
        """
        await self._ensure_indexes()

        collection = self._db.long_tasks
        task_dict = task.to_dict()

        try:
            result = await collection.insert_one(task_dict)
            logger.info(f"Created long task: task_id={task.task_id}, user_id={task.user_id}")
            return task.task_id
        except Exception as e:
            # Check if it's a duplicate key error
            if "duplicate key" in str(e).lower() or "E11000" in str(e):
                logger.warning(
                    f"Task already exists (idempotent): task_id={task.task_id}, user_id={task.user_id}"
                )
                return task.task_id
            raise

    async def pick_next_queued(self) -> LongSummarizationTask | None:
        """Pick next queued task for processing.

        Purpose:
            Atomically finds and marks a queued task as running.
            Prevents double-processing by using atomic update.

        Returns:
            LongSummarizationTask if found, None otherwise
        """
        await self._ensure_indexes()

        collection = self._db.long_tasks

        # Atomic find and update to prevent race conditions
        result = await collection.find_one_and_update(
            {"status": TaskStatus.QUEUED.value},
            {
                "$set": {
                    "status": TaskStatus.RUNNING.value,
                    "started_at": datetime.utcnow(),
                }
            },
            sort=[("created_at", 1)],  # Oldest first
            return_document=ReturnDocument.AFTER,
        )

        if not result:
            return None

        try:
            task = LongSummarizationTask.from_dict(result)
            logger.info(f"Picked queued task: task_id={task.task_id}, user_id={task.user_id}")
            return task
        except Exception as e:
            logger.error(
                f"Failed to deserialize task: task_id={result.get('task_id')}, error={e}",
                exc_info=True,
            )
            # Mark as failed if deserialization fails
            await collection.update_one(
                {"task_id": result.get("task_id")},
                {
                    "$set": {
                        "status": TaskStatus.FAILED.value,
                        "error": f"Deserialization error: {str(e)}",
                        "finished_at": datetime.utcnow(),
                    }
                },
            )
            return None

    async def mark_running(self, task_id: str) -> None:
        """Mark task as running (idempotent).

        Args:
            task_id: Task ID
        """
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
            logger.info(f"Marked task as running: task_id={task_id}")
        else:
            logger.debug(f"Task already running or not queued: task_id={task_id}")

    async def complete(self, task_id: str, result_text: str) -> None:
        """Mark task as succeeded with result.

        Args:
            task_id: Task ID
            result_text: Generated summary text
        """
        await self._ensure_indexes()

        collection = self._db.long_tasks
        result = await collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.SUCCEEDED.value,
                    "result_text": result_text,
                    "finished_at": datetime.utcnow(),
                }
            },
        )

        if result.modified_count > 0:
            logger.info(f"Marked task as succeeded: task_id={task_id}, result_length={len(result_text)}")
        else:
            logger.warning(f"Task not found or already completed: task_id={task_id}")

    async def fail(self, task_id: str, error: str) -> None:
        """Mark task as failed with error.

        Args:
            task_id: Task ID
            error: Error message
        """
        await self._ensure_indexes()

        collection = self._db.long_tasks
        result = await collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.FAILED.value,
                    "error": error[:1000],  # Limit error length
                    "finished_at": datetime.utcnow(),
                }
            },
        )

        if result.modified_count > 0:
            logger.warning(f"Marked task as failed: task_id={task_id}, error={error[:100]}")
        else:
            logger.warning(f"Task not found: task_id={task_id}")

    async def get_by_id(self, task_id: str) -> LongSummarizationTask | None:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            LongSummarizationTask if found, None otherwise
        """
        await self._ensure_indexes()

        collection = self._db.long_tasks
        result = await collection.find_one({"task_id": task_id})

        if not result:
            return None

        try:
            return LongSummarizationTask.from_dict(result)
        except Exception as e:
            logger.error(f"Failed to deserialize task: task_id={task_id}, error={e}", exc_info=True)
            return None

    async def get_by_user(
        self, user_id: int, limit: int = 10, status: TaskStatus | None = None
    ) -> list[LongSummarizationTask]:
        """Get tasks by user ID.

        Args:
            user_id: User ID
            limit: Maximum number of tasks to return
            status: Optional status filter

        Returns:
            List of LongSummarizationTask
        """
        await self._ensure_indexes()

        collection = self._db.long_tasks
        query: dict[str, Any] = {"user_id": user_id}
        if status:
            query["status"] = status.value

        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        tasks = []

        async for doc in cursor:
            try:
                task = LongSummarizationTask.from_dict(doc)
                tasks.append(task)
            except Exception as e:
                logger.error(f"Failed to deserialize task: error={e}", exc_info=True)

        return tasks

