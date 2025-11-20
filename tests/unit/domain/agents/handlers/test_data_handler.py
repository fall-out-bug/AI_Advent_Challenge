"""Unit tests for Data Handler.

Following TDD principles and testing best practices.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.dtos.butler_dialog_dtos import DialogContext, DialogState
from src.presentation.bot.handlers.data import DataHandler


class MockToolClient:
    """Mock tool client."""

    def __init__(self):
        self.call_tool = AsyncMock()

    async def discover_tools(self):
        """Mock discover_tools."""
        return []


class TestDataHandler:
    """Test DataHandler."""

    @pytest.fixture
    def mock_tool_client(self):
        """Create mock tool client."""
        return MockToolClient()

    @pytest.fixture
    def handler(self, mock_tool_client):
        """Create handler instance."""
        return DataHandler(tool_client=mock_tool_client)

    @pytest.mark.asyncio
    async def test_handle_gets_channels_digest(self, handler, mock_tool_client):
        """Test getting channels digest."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_tool_client.call_tool.return_value = {
            "digests": [{"channel": "test", "summary": "Test summary"}]
        }
        response = await handler.handle(context, "Show channel digest")
        assert "digest" in response.lower() or "дайджест" in response.lower()
        mock_tool_client.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_gets_student_stats(self, handler, mock_tool_client):
        """Test getting student stats."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_tool_client.call_tool.return_value = {
            "stats": {"students": 10, "active": 8}
        }
        response = await handler.handle(context, "Show student stats")
        assert "statistic" in response.lower() or "stats" in response.lower()
        mock_tool_client.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_handles_empty_digest(self, handler, mock_tool_client):
        """Test handling empty digest."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_tool_client.call_tool.return_value = {"digests": []}
        response = await handler.handle(context, "Show digest")
        lower_response = response.lower()
        assert (
            "no" in lower_response
            or "available" in lower_response
            or "нет" in lower_response
        )

    @pytest.mark.asyncio
    async def test_handle_handles_error(self, handler, mock_tool_client):
        """Test error handling."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_tool_client.call_tool = AsyncMock(side_effect=Exception("Error"))
        response = await handler.handle(context, "Show data")
        lower_response = response.lower()
        assert (
            "failed" in lower_response
            or "error" in lower_response
            or "не удалось" in lower_response
        )
