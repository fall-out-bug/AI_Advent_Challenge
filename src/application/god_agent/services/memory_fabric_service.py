"""Memory Fabric Service implementation."""

from typing import Any, Dict, List

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.interfaces.memory_repository import IGodAgentMemoryRepository
from src.domain.interfaces.personalization import UserProfileRepository
from src.domain.personalization.memory_slice import MemorySlice
from src.domain.personalization.user_memory_event import UserMemoryEvent
from src.domain.personalization.user_profile import UserProfile
from src.infrastructure.logging import get_logger

logger = get_logger("memory_fabric_service")

COMPRESSION_THRESHOLD = 50
COMPRESSION_KEEP_EVENTS = 20


class MemoryFabricService:
    """Service for aggregating memory fabric.

    Purpose:
        Aggregates user profile, conversation summary, RAG hits, and
        artifact references into MemorySnapshot with TTL/compression.

    Attributes:
        profile_repo: Repository for user profiles.
        memory_repo: Repository for memory events and God Agent data.

    Example:
        >>> service = MemoryFabricService(profile_repo, memory_repo)
        >>> snapshot = await service.get_memory_snapshot("user_1")
        >>> snapshot.user_id
        'user_1'
    """

    def __init__(
        self,
        profile_repo: UserProfileRepository,
        memory_repo: IGodAgentMemoryRepository,
    ) -> None:
        """Initialize service with repositories.

        Args:
            profile_repo: Repository for user profiles.
            memory_repo: Repository for memory events and God Agent data.
        """
        self.profile_repo = profile_repo
        self.memory_repo = memory_repo
        logger.info("MemoryFabricService initialized")

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
        # Load profile
        profile = await self.profile_repo.get(user_id)
        profile_summary = self._format_profile_summary(profile)

        # Load memory events
        events = await self.memory_repo.get_recent_events(user_id, limit=20)
        memory_slice = MemorySlice(events=events)
        conversation_summary = memory_slice.to_prompt_context(max_events=20)

        # Load artifact references
        artifact_refs: List[str] = []
        artifact_types = ["code_diff", "review", "test_result"]
        for artifact_type in artifact_types:
            refs = await self.memory_repo.get_artifact_refs(user_id, artifact_type)
            artifact_refs.extend(refs)

        # Use provided RAG hits or empty list
        rag_hits_list = rag_hits or []

        snapshot = MemorySnapshot(
            user_id=user_id,
            profile_summary=profile_summary,
            conversation_summary=conversation_summary,
            rag_hits=rag_hits_list,
            artifact_refs=artifact_refs,
        )

        logger.info(
            "Memory snapshot retrieved",
            extra={
                "user_id": user_id,
                "events_count": len(events),
                "rag_hits_count": len(rag_hits_list),
                "artifact_refs_count": len(artifact_refs),
            },
        )

        return snapshot

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
        await self.memory_repo.append_events([event])

        # Check if compression needed
        count = await self.memory_repo.count_events(user_id)
        if count > COMPRESSION_THRESHOLD:
            logger.info(
                "Memory threshold exceeded, triggering compression",
                extra={"user_id": user_id, "event_count": count},
            )
            await self.compress_memory(user_id)

        logger.debug(
            "Memory updated",
            extra={"user_id": user_id, "event_id": str(event.event_id)},
        )

    async def compress_memory(self, user_id: str) -> None:
        """Compress memory when threshold exceeded.

        Purpose:
            Compress memory when >50 events, keeping last 20.

        Args:
            user_id: User identifier.

        Example:
            >>> await service.compress_memory("user_1")
        """
        count = await self.memory_repo.count_events(user_id)

        if count <= COMPRESSION_THRESHOLD:
            logger.debug(
                "Compression not needed",
                extra={"user_id": user_id, "event_count": count},
            )
            return

        # Get recent events for summary
        events = await self.memory_repo.get_recent_events(
            user_id, limit=COMPRESSION_KEEP_EVENTS
        )
        summary = self._create_compression_summary(events)

        # Compress: keep last 20 events
        await self.memory_repo.compress(
            user_id, summary, keep_last_n=COMPRESSION_KEEP_EVENTS
        )

        # Update profile with summary
        profile = await self.profile_repo.get(user_id)
        if profile:
            updated_profile = profile.with_summary(summary)
            await self.profile_repo.save(updated_profile)

        logger.info(
            "Memory compressed",
            extra={
                "user_id": user_id,
                "before_count": count,
                "after_count": COMPRESSION_KEEP_EVENTS,
            },
        )

    def _format_profile_summary(self, profile: UserProfile | None) -> str:
        """Format user profile as summary string.

        Args:
            profile: User profile or None.

        Returns:
            Formatted profile summary.
        """
        if profile is None:
            return ""

        parts = [
            f"Persona: {profile.persona}",
            f"Language: {profile.language}",
            f"Tone: {profile.tone}",
        ]

        if profile.preferred_topics:
            topics = ", ".join(profile.preferred_topics)
            parts.append(f"Interests: {topics}")

        if profile.memory_summary:
            parts.append(f"Previous summary: {profile.memory_summary}")

        return " | ".join(parts)

    def _create_compression_summary(self, events: List[UserMemoryEvent]) -> str:
        """Create summary from events for compression.

        Args:
            events: List of events to summarize.

        Returns:
            Compression summary string.
        """
        if not events:
            return "No recent interactions"

        # Simple summary: count and topics
        user_messages = [e for e in events if e.role == "user"]
        assistant_messages = [e for e in events if e.role == "assistant"]

        summary_parts = [
            f"{len(user_messages)} user messages",
            f"{len(assistant_messages)} assistant responses",
        ]

        return ", ".join(summary_parts)
