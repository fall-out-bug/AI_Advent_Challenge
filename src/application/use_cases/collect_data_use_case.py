"""Data collection use case for Butler flows."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.application.dtos.butler_use_case_dtos import DigestResult, StatsResult
from src.domain.interfaces.tool_client import ToolClientProtocol

logger = logging.getLogger(__name__)


class CollectDataUseCase:
    """Collect digests and statistics via MCP tools."""

    def __init__(self, tool_client: ToolClientProtocol) -> None:
        self._tool_client = tool_client

    async def get_channels_digest(
        self, user_id: int, hours: Optional[int] = None
    ) -> DigestResult:
        """Fetch channel digests for the given user."""

        try:
            params: Dict[str, Any] = {"user_id": user_id}
            if hours is not None:
                params["hours"] = hours

            response = await self._tool_client.call_tool("get_channel_digest", params)

            digests: List[Dict[str, Any]] = []
            if isinstance(response, dict):
                if "digests" in response:
                    digests = list(response.get("digests") or [])
                    if not digests and response.get("digest"):
                        digests = [response.get("digest")]
                elif response.get("digest"):
                    digests = [response.get("digest")]
                elif response:
                    digests = [response]
            elif isinstance(response, list):
                digests = response

            return DigestResult(digests=digests)
        except Exception as error:  # noqa: BLE001
            logger.error(
                "Channel digest retrieval failed",
                exc_info=True,
                extra={"user_id": user_id, "error": str(error)},
            )
            return DigestResult(error=f"Failed to get channels digest: {error}")

    async def get_student_stats(self, teacher_id: Any) -> StatsResult:
        """Fetch student statistics for the given teacher."""

        try:
            response = await self._tool_client.call_tool(
                "get_student_stats", {"teacher_id": teacher_id}
            )
            if isinstance(response, dict):
                stats = response.get("stats", {})
            else:
                stats = {}
            return StatsResult(stats=stats)
        except Exception as error:  # noqa: BLE001
            logger.error(
                "Student stats retrieval failed",
                exc_info=True,
                extra={"teacher_id": teacher_id, "error": str(error)},
            )
            return StatsResult(error=f"Failed to get student stats: {error}")
