"""Real external API client for review publishing."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.domain.interfaces.review_publisher import ReviewPublisher
from src.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class ExternalAPIClient(ReviewPublisher):
    """Real external API client for publishing reviews.

    Purpose:
        Publishes review results to external API service.
        Uses HTTP client with retry logic and error handling.

    Args:
        settings: Application settings with API configuration
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize external API client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.url = settings.external_api_url
        self.api_key = settings.external_api_key
        self.timeout = settings.external_api_timeout

        if not self.url:
            raise ValueError("external_api_url must be set in settings")

        if not self.api_key:
            raise ValueError("external_api_key must be set in settings")

    async def publish_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Publish review result to external system.

        Args:
            payload: Review result payload with all data

        Returns:
            Response dictionary with status and external_id

        Raises:
            httpx.HTTPError: On HTTP request failure
            ValueError: If API URL or key is not configured
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.url}/reviews",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

                logger.info(
                    f"Published review to external API: "
                    f"task_id={payload.get('task_id')}, "
                    f"external_id={result.get('external_id')}"
                )

                return {
                    "status": "published",
                    "external_id": result.get("external_id"),
                    "response": result,
                }

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"External API returned error: {e.response.status_code}, "
                    f"response={e.response.text}"
                )
                raise
            except httpx.RequestError as e:
                logger.error(f"External API request failed: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error publishing to external API: {e}")
                raise
