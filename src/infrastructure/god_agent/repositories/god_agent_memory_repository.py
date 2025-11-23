"""Mongo-backed God Agent memory repository."""

from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from src.domain.god_agent.interfaces.memory_repository import IGodAgentMemoryRepository
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository,
)

logger = get_logger("god_agent_memory_repository")


class GodAgentMemoryRepository(MongoUserMemoryRepository):
    """Mongo-backed repository extending UserMemoryRepository with God Agent features.

    Purpose:
        Extends MongoUserMemoryRepository with task timeline tracking and
        artifact references. Maintains compatibility with UserMemoryRepository.

    Attributes:
        task_timeline_collection: MongoDB collection for task timelines.
        artifact_refs_collection: MongoDB collection for artifact references.

    Example:
        >>> repo = GodAgentMemoryRepository(client, "butler")
        >>> timeline = {"task_id": "task_1", "steps": []}
        >>> await repo.save_task_timeline("user_1", "task_1", timeline)
    """

    def __init__(
        self, mongo_client: AsyncIOMotorClient, database: str = "butler"  # type: ignore[type-arg]
    ) -> None:
        """Initialize repository with Mongo client.

        Args:
            mongo_client: Motor async Mongo client.
            database: Database name (default: "butler").
        """
        super().__init__(mongo_client, database)
        self.task_timeline_collection = mongo_client[database][
            "god_agent_task_timeline"
        ]
        self.artifact_refs_collection = mongo_client[database][
            "god_agent_artifact_refs"
        ]
        logger.info(
            "GodAgentMemoryRepository initialized",
            extra={
                "database": database,
                "collections": [
                    "user_memory",
                    "god_agent_task_timeline",
                    "god_agent_artifact_refs",
                ],
            },
        )

    async def save_task_timeline(
        self, user_id: str, task_id: str, timeline: Dict[str, Any]
    ) -> None:
        """Save task timeline for a user.

        Purpose:
            Store task execution timeline with steps, status, and metadata.
            Uses upsert to update existing timelines.

        Args:
            user_id: User identifier.
            task_id: Task identifier.
            timeline: Timeline dictionary with task execution data.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> timeline = {
            ...     "task_id": "task_123",
            ...     "steps": [{"step_id": "step1", "status": "completed"}],
            ... }
            >>> await repo.save_task_timeline("user_1", "task_123", timeline)
        """
        try:
            doc = {
                "user_id": user_id,
                "task_id": task_id,
                "timeline": timeline,
            }
            await self.task_timeline_collection.update_one(  # type: ignore
                {"user_id": user_id, "task_id": task_id},
                {"$set": doc},
                upsert=True,
            )

            logger.info(
                "Task timeline saved",
                extra={"user_id": user_id, "task_id": task_id},
            )

        except PyMongoError as e:
            logger.error(
                "Failed to save task timeline",
                extra={
                    "user_id": user_id,
                    "task_id": task_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def get_task_timeline(
        self, user_id: str, task_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get task timeline for a user.

        Purpose:
            Retrieve stored task timeline by user and task ID.

        Args:
            user_id: User identifier.
            task_id: Task identifier.

        Returns:
            Timeline dictionary if found, None otherwise.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> timeline = await repo.get_task_timeline("user_1", "task_123")
            >>> timeline["task_id"]
            'task_123'
        """
        try:
            doc = await self.task_timeline_collection.find_one(
                {"user_id": user_id, "task_id": task_id}
            )

            if doc is None:
                logger.debug(
                    "Task timeline not found",
                    extra={"user_id": user_id, "task_id": task_id},
                )
                return None

            timeline = doc.get("timeline", {})
            logger.debug(
                "Task timeline retrieved",
                extra={"user_id": user_id, "task_id": task_id},
            )
            return timeline if isinstance(timeline, dict) else {}

        except PyMongoError as e:
            logger.error(
                "Failed to get task timeline",
                extra={
                    "user_id": user_id,
                    "task_id": task_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def save_artifact_ref(
        self, user_id: str, artifact_type: str, ref: str
    ) -> None:
        """Save artifact reference for a user.

        Purpose:
            Store reference to an artifact (code diff, review, etc.) for later
            retrieval. Uses upsert to avoid duplicates.

        Args:
            user_id: User identifier.
            artifact_type: Type of artifact (e.g., "code_diff", "review").
            ref: Artifact reference (e.g., commit hash, file path).

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> await repo.save_artifact_ref(
            ...     "user_1", "code_diff", "commit_hash_abc123"
            ... )
        """
        try:
            doc = {
                "user_id": user_id,
                "artifact_type": artifact_type,
                "ref": ref,
            }
            await self.artifact_refs_collection.update_one(
                {"user_id": user_id, "artifact_type": artifact_type, "ref": ref},
                {"$set": doc},
                upsert=True,
            )

            logger.info(
                "Artifact reference saved",
                extra={
                    "user_id": user_id,
                    "artifact_type": artifact_type,
                    "ref": ref,
                },
            )

        except PyMongoError as e:
            logger.error(
                "Failed to save artifact reference",
                extra={
                    "user_id": user_id,
                    "artifact_type": artifact_type,
                    "ref": ref,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def get_artifact_refs(self, user_id: str, artifact_type: str) -> List[str]:
        """Get artifact references for a user.

        Purpose:
            Retrieve all artifact references of a given type for a user.

        Args:
            user_id: User identifier.
            artifact_type: Type of artifact (e.g., "code_diff", "review").

        Returns:
            List of artifact references.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> refs = await repo.get_artifact_refs("user_1", "code_diff")
            >>> len(refs) >= 0
            True
        """
        try:
            cursor = self.artifact_refs_collection.find(
                {"user_id": user_id, "artifact_type": artifact_type}
            )

            docs = await cursor.to_list(length=None)
            refs = [doc["ref"] for doc in docs]

            logger.debug(
                "Artifact references retrieved",
                extra={
                    "user_id": user_id,
                    "artifact_type": artifact_type,
                    "count": len(refs),
                },
            )

            return refs

        except PyMongoError as e:
            logger.error(
                "Failed to get artifact references",
                extra={
                    "user_id": user_id,
                    "artifact_type": artifact_type,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise
