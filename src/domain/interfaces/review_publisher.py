"""Review publisher protocol interface."""

from __future__ import annotations

from typing import Any, Protocol


class ReviewPublisher(Protocol):
    """Protocol for publishing review results.

    Purpose:
        Defines interface for publishing review results to external
        systems. Allows mock and real implementations.
    """

    async def publish_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Publish review result to external system.

        Args:
            payload: Review result payload with all data

        Returns:
            Response dictionary with status and external_id

        Raises:
            Exception: On publish failure
        """
        ...
