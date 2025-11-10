"""Homework checker client protocol."""

from __future__ import annotations

from typing import Any, Protocol


class HomeworkCheckerProtocol(Protocol):
    """Protocol describing interactions with homework checker service.

    Purpose:
        Provide an abstract contract for components that can list recent
        homework submissions and download submission archives. Implementations
        live in the infrastructure layer (e.g., HTTP clients).

    Example:
        >>> class FakeChecker(HomeworkCheckerProtocol):
        ...     async def get_recent_commits(self, days: int) -> dict[str, Any]:
        ...         return {"total": 0, "commits": []}
        ...     async def download_archive(self, commit_hash: str) -> bytes:
        ...         return b""
    """

    async def get_recent_commits(self, days: int) -> dict[str, Any]:
        """Return metadata about homework submissions for the given window."""

    async def download_archive(self, commit_hash: str) -> bytes:
        """Return ZIP archive bytes for the provided commit hash."""
