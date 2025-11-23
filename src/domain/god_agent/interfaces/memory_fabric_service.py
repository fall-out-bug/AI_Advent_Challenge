"""Memory Fabric Service interface."""

from typing import Any, Dict, List, Protocol

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.personalization.user_memory_event import UserMemoryEvent


class IMemoryFabricService(Protocol):
    """Service interface for aggregating memory fabric.

    Purpose:
        Aggregates user profile, conversation summary, RAG hits, and
        artifact references into MemorySnapshot with TTL/compression.
    """

    async def get_memory_snapshot(
        self, user_id: str, rag_hits: List[Dict[str, Any]] | None = None
    ) -> MemorySnapshot:
        """Get memory snapshot for a user.

        Purpose:
            Aggregate all memory sources (profile, events, RAG hits, artifacts)
            into a single MemorySnapshot.

        Args:
            user_id: User identifier.
            rag_hits: Optional RAG search results.

        Returns:
            MemorySnapshot with all aggregated data.

        Example:
            >>> snapshot = await service.get_memory_snapshot("user_1")
            >>> snapshot.user_id
            'user_1'
        """
        ...

    async def update_memory(self, user_id: str, event: UserMemoryEvent) -> None:
        """Update memory with new event.

        Purpose:
            Add new memory event and trigger compression if needed.

        Args:
            user_id: User identifier.
            event: New memory event.

        Example:
            >>> event = UserMemoryEvent.create_user_event("user_1", "Hello")
            >>> await service.update_memory("user_1", event)
        """
        ...

    async def compress_memory(self, user_id: str) -> None:
        """Compress memory when threshold exceeded.

        Purpose:
            Compress memory when >50 events, keeping last 20.

        Args:
            user_id: User identifier.

        Example:
            >>> await service.compress_memory("user_1")
        """
        ...
