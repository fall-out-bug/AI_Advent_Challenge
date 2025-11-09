"""Tests for CollectDataUseCase."""

import pytest
from unittest.mock import AsyncMock

from src.application.usecases.collect_data_usecase import CollectDataUseCase
from src.application.usecases.result_types import DigestResult, StatsResult
from src.domain.interfaces.tool_client import ToolClientProtocol


class TestCollectDataUseCase:
    """Test suite for CollectDataUseCase."""

    @pytest.fixture
    def mock_tool_client(self):
        """Create mock ToolClientProtocol."""
        return AsyncMock(spec=ToolClientProtocol)

    @pytest.fixture
    def usecase(self, mock_tool_client):
        """Create CollectDataUseCase instance."""
        return CollectDataUseCase(tool_client=mock_tool_client)

    @pytest.mark.asyncio
    async def test_get_channels_digest_success(self, usecase, mock_tool_client):
        """Test successful channel digest retrieval."""
        digests = [
            {
                "channel": "python",
                "summary": "Python news",
                "post_count": 5,
            },
            {
                "channel": "ai",
                "summary": "AI updates",
                "post_count": 3,
            },
        ]
        mock_tool_client.call_tool.return_value = {
            "digests": digests,
            "generated_at": "2025-01-01T12:00:00Z",
        }

        result = await usecase.get_channels_digest(user_id=123)

        assert isinstance(result, DigestResult)
        assert len(result.digests) == 2
        assert result.digests[0]["channel"] == "python"
        assert result.error is None
        mock_tool_client.call_tool.assert_called_once_with(
            "get_channel_digest", {"user_id": 123}
        )

    @pytest.mark.asyncio
    async def test_get_channels_digest_empty(self, usecase, mock_tool_client):
        """Test empty channel digest result."""
        mock_tool_client.call_tool.return_value = {
            "digests": [],
            "generated_at": "2025-01-01T12:00:00Z",
        }

        result = await usecase.get_channels_digest(user_id=123)

        assert isinstance(result, DigestResult)
        assert result.digests == []
        assert result.error is None

    @pytest.mark.asyncio
    async def test_get_channels_digest_error(self, usecase, mock_tool_client):
        """Test error handling for channel digest."""
        mock_tool_client.call_tool.side_effect = Exception("MCP error")

        result = await usecase.get_channels_digest(user_id=123)

        assert isinstance(result, DigestResult)
        assert result.digests == []
        assert result.error is not None
        assert "MCP error" in result.error

    @pytest.mark.asyncio
    async def test_get_student_stats_success(self, usecase, mock_tool_client):
        """Test successful student stats retrieval."""
        stats = {
            "total_students": 25,
            "active_students": 20,
            "average_score": 85.5,
        }
        mock_tool_client.call_tool.return_value = {"stats": stats}

        result = await usecase.get_student_stats(teacher_id=456)

        assert isinstance(result, StatsResult)
        assert result.stats["total_students"] == 25
        assert result.stats["active_students"] == 20
        assert result.error is None
        mock_tool_client.call_tool.assert_called_once_with(
            "get_student_stats", {"teacher_id": 456}
        )

    @pytest.mark.asyncio
    async def test_get_student_stats_empty(self, usecase, mock_tool_client):
        """Test empty student stats result."""
        mock_tool_client.call_tool.return_value = {"stats": {}}

        result = await usecase.get_student_stats(teacher_id=456)

        assert isinstance(result, StatsResult)
        assert result.stats == {}
        assert result.error is None

    @pytest.mark.asyncio
    async def test_get_student_stats_error(self, usecase, mock_tool_client):
        """Test error handling for student stats."""
        mock_tool_client.call_tool.side_effect = Exception("MCP error")

        result = await usecase.get_student_stats(teacher_id=456)

        assert isinstance(result, StatsResult)
        assert result.stats == {}
        assert result.error is not None
        assert "MCP error" in result.error

    @pytest.mark.asyncio
    async def test_get_student_stats_tool_not_found(self, usecase, mock_tool_client):
        """Test when student stats tool doesn't exist."""
        # Tool might not exist, return empty result
        mock_tool_client.call_tool.side_effect = Exception("Tool not found")

        result = await usecase.get_student_stats(teacher_id=456)

        assert isinstance(result, StatsResult)
        assert result.error is not None
