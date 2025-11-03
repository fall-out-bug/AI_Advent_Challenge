"""Use case for collecting data (channels digests, student stats).

Following Clean Architecture: Business logic separated from presentation.
"""

import logging
from typing import Dict, Any

from src.application.usecases.result_types import DigestResult, StatsResult
from src.domain.interfaces.tool_client import ToolClientProtocol

logger = logging.getLogger(__name__)


class CollectDataUseCase:
    """Use case for collecting data summaries.

    Purpose:
        Encapsulates business logic for data collection: channel digests
        and student statistics retrieval via MCP tools.

    Example:
        >>> usecase = CollectDataUseCase(tool_client)
        >>> digest_result = await usecase.get_channels_digest(user_id=123)
        >>> if digest_result.digests:
        ...     print(f"Found {len(digest_result.digests)} digests")
    """

    def __init__(self, tool_client: ToolClientProtocol):
        """Initialize use case.

        Args:
            tool_client: MCP tool client for data collection
        """
        self.tool_client = tool_client

    async def get_channels_digest(self, user_id: int) -> DigestResult:
        """Get channel digests for user."""
        try:
            result = await self.tool_client.call_tool("get_channel_digest", {"user_id": user_id})
            return DigestResult(digests=result.get("digests", []))
        except Exception as e:
            logger.error(f"Failed to get channels digest: {e}", exc_info=True)
            return DigestResult(error=f"Failed to get channels digest: {str(e)}")

    async def get_student_stats(self, teacher_id: int) -> StatsResult:
        """Get student statistics for teacher."""
        try:
            result = await self.tool_client.call_tool("get_student_stats", {"teacher_id": teacher_id})
            return StatsResult(stats=result.get("stats", {}))
        except Exception as e:
            logger.error(f"Failed to get student stats: {e}", exc_info=True)
            return StatsResult(error=f"Failed to get student stats: {str(e)}")

