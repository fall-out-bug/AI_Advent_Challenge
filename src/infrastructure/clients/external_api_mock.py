"""Mock external API client for review publishing."""

from __future__ import annotations

import logging
from typing import Any

from src.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class ExternalAPIClientMock:
    """Mock external API client.

    Purpose:
        Logs review publishing requests without making actual HTTP calls.
        Used when external API is not available or for testing.

    Args:
        settings: Application settings
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize mock client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.enabled = settings.external_api_enabled

    async def publish_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Publish review (mock implementation).

        Args:
            payload: Review payload

        Returns:
            Mock response with status
        """
        logger.info(
            f"Mock external API publish: task_id={payload.get('task_id')}, "
            f"student_id={payload.get('student_id')}"
        )
        return {
            "status": "published",
            "external_id": f"mock_{payload.get('task_id', 'unknown')}",
            "response": {"mock": True},
        }
