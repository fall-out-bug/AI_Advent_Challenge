"""Unit tests for Task Handler.

Following TDD principles and testing best practices.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.domain.agents.handlers.task_handler import TaskHandler
from src.domain.agents.state_machine import DialogContext, DialogState
from src.domain.entities.intent import IntentParseResult


class MockToolClient:
    """Mock tool client."""

    def __init__(self):
        self.call_tool = AsyncMock()

    async def discover_tools(self):
        """Mock discover_tools."""
        return []


class TestTaskHandler:
    """Test TaskHandler."""

    @pytest.fixture
    def mock_intent_orchestrator(self):
        """Create mock intent orchestrator."""
        orchestrator = Mock(spec=IntentOrchestrator)
        result = IntentParseResult(
            title="Test task",
            description="Test description",
            needs_clarification=False,
        )
        orchestrator.parse_task_intent = AsyncMock(return_value=result)
        return orchestrator

    @pytest.fixture
    def mock_tool_client(self):
        """Create mock tool client."""
        return MockToolClient()

    @pytest.fixture
    def handler(self, mock_intent_orchestrator, mock_tool_client):
        """Create handler instance."""
        return TaskHandler(
            intent_orchestrator=mock_intent_orchestrator,
            tool_client=mock_tool_client,
        )

    @pytest.mark.asyncio
    async def test_handle_creates_task_successfully(
        self, handler, mock_intent_orchestrator, mock_tool_client
    ):
        """Test successful task creation."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_tool_client.call_tool.return_value = {"id": "task123"}
        response = await handler.handle(context, "Create a task")
        assert "created successfully" in response.lower()
        mock_tool_client.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_asks_for_clarification(
        self, handler, mock_intent_orchestrator, mock_tool_client
    ):
        """Test clarification request."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        result = IntentParseResult(
            title="Test",
            needs_clarification=True,
            questions=["What is the deadline?"],
        )
        mock_intent_orchestrator.parse_task_intent = AsyncMock(return_value=result)
        response = await handler.handle(context, "Create task")
        assert "?" in response or "clarif" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_handles_error(
        self, handler, mock_intent_orchestrator
    ):
        """Test error handling."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_intent_orchestrator.parse_task_intent = AsyncMock(
            side_effect=Exception("Error")
        )
        response = await handler.handle(context, "Create task")
        assert "sorry" in response.lower() or "error" in response.lower()

