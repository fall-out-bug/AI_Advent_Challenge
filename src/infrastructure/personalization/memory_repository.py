"""Mongo-backed user memory repository."""

import time
from datetime import datetime
from typing import Any, List
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from src.domain.interfaces.personalization import UserMemoryRepository
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.metrics import (
    user_memory_compression_duration_seconds,
    user_memory_compressions_total,
    user_memory_events_total,
)

logger = get_logger("memory_repository")


class MongoUserMemoryRepository:
    """Mongo-backed repository for user memory events.

    Purpose:
        Implements UserMemoryRepository protocol using MongoDB.
        Stores conversation history with chronological ordering.

    Attributes:
        collection: MongoDB collection for user_memory.

    Example:
        >>> repo = MongoUserMemoryRepository(client, "butler")
        >>> events = await repo.get_recent_events("123", limit=10)
    """

    def __init__(
        self, mongo_client: AsyncIOMotorClient, database: str = "butler"  # type: ignore[type-arg]
    ) -> None:
        """Initialize repository with Mongo client.

        Args:
            mongo_client: Motor async Mongo client.
            database: Database name (default: "butler").
        """
        self.collection = mongo_client[database]["user_memory"]
        logger.info(
            "MongoUserMemoryRepository initialized",
            extra={"database": database, "collection": "user_memory"},
        )

    async def append_events(self, events: List[UserMemoryEvent]) -> None:
        """Append new memory events.

        Purpose:
            Insert new events into MongoDB in batch.

        Args:
            events: List of events to append.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> event = UserMemoryEvent.create_user_event("123", "Hello")
            >>> await repo.append_events([event])
        """
        if not events:
            return

        try:
            docs = [self._event_to_doc(e) for e in events]
            await self.collection.insert_many(docs)

            # Update metrics
            for event in events:
                user_memory_events_total.labels(role=event.role).inc()

            logger.info(
                "Memory events appended",
                extra={
                    "user_id": events[0].user_id,
                    "count": len(events),
                    "roles": [e.role for e in events],
                },
            )

        except PyMongoError as e:
            logger.error(
                "Failed to append events",
                extra={
                    "user_id": events[0].user_id if events else None,
                    "count": len(events),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def get_recent_events(
        self, user_id: str, limit: int
    ) -> List[UserMemoryEvent]:
        """Get recent events in chronological order.

        Purpose:
            Retrieve most recent N events for context building.
            Returns in chronological order (oldest first).

        Args:
            user_id: User identifier.
            limit: Maximum events to return.

        Returns:
            List of recent events (chronological order).

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> events = await repo.get_recent_events("123", limit=20)
            >>> len(events) <= 20
            True
        """
        try:
            # Query with descending sort, then reverse
            cursor = (
                self.collection.find({"user_id": user_id})
                .sort("created_at", -1)
                .limit(limit)
            )

            docs = await cursor.to_list(length=limit)
            events = [self._doc_to_event(d) for d in docs]

            # Reverse to chronological order
            events_chronological = list(reversed(events))

            logger.debug(
                "Recent events loaded",
                extra={
                    "user_id": user_id,
                    "requested_limit": limit,
                    "actual_count": len(events_chronological),
                },
            )

            return events_chronological

        except PyMongoError as e:
            logger.error(
                "Failed to get recent events",
                extra={"user_id": user_id, "limit": limit, "error": str(e)},
                exc_info=True,
            )
            raise

    async def compress(self, user_id: str, summary: str, keep_last_n: int) -> None:
        """Compress memory by deleting old events.

        Purpose:
            Delete older events while keeping recent N events.
            Summary of deleted content stored in user profile.

        Args:
            user_id: User identifier.
            summary: Summary of deleted events (stored separately).
            keep_last_n: Number of recent events to retain.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> await repo.compress("123", "User talked about Python", 20)
        """
        start_time = time.time()

        try:
            # Get all events sorted descending
            cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)

            all_events = await cursor.to_list(length=None)

            if len(all_events) <= keep_last_n:
                logger.info(
                    "No compression needed",
                    extra={"user_id": user_id, "event_count": len(all_events)},
                )
                return

            # Keep last N, delete rest
            keep_ids = [e["_id"] for e in all_events[:keep_last_n]]
            result = await self.collection.delete_many(
                {"user_id": user_id, "_id": {"$nin": keep_ids}}
            )

            duration = time.time() - start_time
            user_memory_compression_duration_seconds.observe(duration)
            user_memory_compressions_total.labels(status="success").inc()

            logger.info(
                "Memory compressed",
                extra={
                    "user_id": user_id,
                    "deleted_count": result.deleted_count,
                    "kept_count": keep_last_n,
                    "summary_length": len(summary),
                    "duration_seconds": duration,
                },
            )

        except PyMongoError as e:
            user_memory_compressions_total.labels(status="error").inc()
            logger.error(
                "Failed to compress memory",
                extra={
                    "user_id": user_id,
                    "keep_last_n": keep_last_n,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def count_events(self, user_id: str) -> int:
        """Count total events for user.

        Purpose:
            Get event count for compression threshold checks.

        Args:
            user_id: User identifier.

        Returns:
            Total event count.

        Raises:
            PyMongoError: If MongoDB operation fails.

        Example:
            >>> count = await repo.count_events("123")
            >>> count >= 0
            True
        """
        try:
            count = await self.collection.count_documents({"user_id": user_id})

            logger.debug(
                "Event count retrieved", extra={"user_id": user_id, "count": count}
            )

            return count

        except PyMongoError as e:
            logger.error(
                "Failed to count events",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise

    def _event_to_doc(self, event: UserMemoryEvent) -> dict[str, Any]:
        """Convert UserMemoryEvent to Mongo document.

        Args:
            event: UserMemoryEvent value object.

        Returns:
            MongoDB document dictionary.
        """
        return {
            "event_id": str(event.event_id),
            "user_id": event.user_id,
            "role": event.role,
            "content": event.content,
            "created_at": event.created_at,
            "tags": event.tags,
        }

    def _doc_to_event(self, doc: dict[str, Any]) -> UserMemoryEvent:
        """Convert Mongo document to UserMemoryEvent.

        Args:
            doc: MongoDB document.

        Returns:
            UserMemoryEvent value object.
        """
        return UserMemoryEvent(
            event_id=UUID(doc["event_id"]),
            user_id=doc["user_id"],
            role=doc["role"],
            content=doc["content"],
            created_at=doc["created_at"],
            tags=doc.get("tags", []),
        )
