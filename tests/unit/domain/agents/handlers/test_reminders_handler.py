"""Unit tests for Reminders Handler.

Following TDD principles and testing best practices.
"""

import pytest
from unittest.mock import AsyncMock

from src.domain.agents.handlers.reminders_handler import RemindersHandler
from src.domain.agents.state_machine import DialogContext, DialogState


class MockToolClient:
    """Mock tool client."""

    def __init__(self):
        self.call_tool = AsyncMock()

    async def discover_tools(self):
        """Mock discover_tools."""
        return []


class TestRemindersHandler:
    """Test RemindersHandler."""

    @pytest.fixture
    def mock_tool_client(self):
        """Create mock tool client."""
        return MockToolClient()

    @pytest.fixture
    def handler(self, mock_tool_client):
        """Create handler instance."""
        return RemindersHandler(tool_client=mock_tool_client)

    @pytest.mark.asyncio
    async def test_handle_lists_reminders(self, handler, mock_tool_client):
        """Test listing reminders."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_tool_client.call_tool.return_value = {
            "reminders": [{"text": "Meeting at 3pm", "time": "2025-01-30T15:00:00Z"}]
        }
        response = await handler.handle(context, "Show reminders")
        assert "reminder" in response.lower()
        mock_tool_client.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_no_reminders(self, handler, mock_tool_client):
        """Test handling no reminders."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_tool_client.call_tool.return_value = {"reminders": []}
        response = await handler.handle(context, "Show reminders")
        assert "no" in response.lower() or "active" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_handles_error(self, handler, mock_tool_client):
        """Test error handling."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_tool_client.call_tool = AsyncMock(side_effect=Exception("Error"))
        response = await handler.handle(context, "Show reminders")
        assert "failed" in response.lower() or "error" in response.lower()
