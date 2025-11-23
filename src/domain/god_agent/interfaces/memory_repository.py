"""God Agent memory repository interface."""

from typing import Any, Dict, List, Optional, Protocol

from src.domain.interfaces.personalization import UserMemoryRepository


class IGodAgentMemoryRepository(UserMemoryRepository, Protocol):
    """Repository interface for God Agent memory with task timeline and artifacts.

    Purpose:
        Extends UserMemoryRepository with God Agent specific functionality:
        task timeline tracking and artifact references.

    Note:
        This interface extends UserMemoryRepository, so implementations must
        support both UserMemoryRepository methods and God Agent specific methods.
    """

    async def save_task_timeline(
        self, user_id: str, task_id: str, timeline: Dict[str, Any]
    ) -> None:
        """Save task timeline for a user.

        Purpose:
            Store task execution timeline with steps, status, and metadata.

        Args:
            user_id: User identifier.
            task_id: Task identifier.
            timeline: Timeline dictionary with task execution data.

        Example:
            >>> timeline = {
            ...     "task_id": "task_123",
            ...     "steps": [{"step_id": "step1", "status": "completed"}],
            ... }
            >>> await repo.save_task_timeline("user_1", "task_123", timeline)
        """
        ...

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

        Example:
            >>> timeline = await repo.get_task_timeline("user_1", "task_123")
            >>> timeline["task_id"]
            'task_123'
        """
        ...

    async def save_artifact_ref(
        self, user_id: str, artifact_type: str, ref: str
    ) -> None:
        """Save artifact reference for a user.

        Purpose:
            Store reference to an artifact (code diff, review, etc.) for later retrieval.

        Args:
            user_id: User identifier.
            artifact_type: Type of artifact (e.g., "code_diff", "review").
            ref: Artifact reference (e.g., commit hash, file path).

        Example:
            >>> await repo.save_artifact_ref(
            ...     "user_1", "code_diff", "commit_hash_abc123"
            ... )
        """
        ...

    async def get_artifact_refs(self, user_id: str, artifact_type: str) -> List[str]:
        """Get artifact references for a user.

        Purpose:
            Retrieve all artifact references of a given type for a user.

        Args:
            user_id: User identifier.
            artifact_type: Type of artifact (e.g., "code_diff", "review").

        Returns:
            List of artifact references.

        Example:
            >>> refs = await repo.get_artifact_refs("user_1", "code_diff")
            >>> len(refs) >= 0
            True
        """
        ...
