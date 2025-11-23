"""MemorySnapshot domain entity."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MemorySnapshot:
    """Memory snapshot domain entity.

    Purpose:
        Aggregates user profile, conversation summary, RAG hits, and
        artifact references for context.

    Attributes:
        user_id: Unique user identifier.
        profile_summary: Compressed user profile summary.
        conversation_summary: Recent conversation summary.
        rag_hits: List of RAG search results with scores.
        artifact_refs: List of artifact references (code diffs, reviews).

    Example:
        >>> snapshot = MemorySnapshot(
        ...     user_id="user1",
        ...     profile_summary="User profile",
        ...     conversation_summary="Recent chat",
        ...     rag_hits=[],
        ...     artifact_refs=[],
        ... )
        >>> snapshot.user_id
        'user1'
    """

    user_id: str
    profile_summary: str
    conversation_summary: str
    rag_hits: List[Dict[str, Any]] = field(default_factory=list)
    artifact_refs: List[str] = field(default_factory=list)

    def compress(self, max_length: int = 100) -> "MemorySnapshot":
        """Compress memory snapshot by truncating summaries.

        Purpose:
            Reduces token usage by truncating long summaries while
            preserving essential information.

        Args:
            max_length: Maximum length for compressed summaries.

        Returns:
            New MemorySnapshot with compressed summaries.

        Example:
            >>> snapshot = MemorySnapshot(
            ...     user_id="user1",
            ...     profile_summary="Long summary " * 100,
            ...     conversation_summary="Conversation",
            ... )
            >>> compressed = snapshot.compress(max_length=50)
            >>> len(compressed.profile_summary) <= 50
            True
        """
        return MemorySnapshot(
            user_id=self.user_id,
            profile_summary=self.profile_summary[:max_length],
            conversation_summary=self.conversation_summary[:max_length],
            rag_hits=self.rag_hits,
            artifact_refs=self.artifact_refs,
        )
