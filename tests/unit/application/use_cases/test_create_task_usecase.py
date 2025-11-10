"""Tests for CreateTaskUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from src.application.dtos.butler_use_case_dtos import TaskCreationResult
from src.application.use_cases.create_task_use_case import CreateTaskUseCase
from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.domain.entities.intent import IntentParseResult
from src.domain.interfaces.tool_client import ToolClientProtocol
from motor.motor_asyncio import AsyncIOMotorDatabase


class TestCreateTaskUseCase:
    """Test suite for CreateTaskUseCase."""

    @pytest.fixture
    def mock_intent_orch(self):
        """Create mock IntentOrchestrator."""
        return AsyncMock(spec=IntentOrchestrator)

    @pytest.fixture
    def mock_tool_client(self):
        """Create mock ToolClientProtocol."""
        return AsyncMock(spec=ToolClientProtocol)

    @pytest.fixture
    def mock_mongodb(self):
        """Create mock MongoDB database."""
        return MagicMock(spec=AsyncIOMotorDatabase)

    @pytest.fixture
    def usecase(self, mock_intent_orch, mock_tool_client, mock_mongodb):
        """Create CreateTaskUseCase instance."""
        return CreateTaskUseCase(
            intent_orchestrator=mock_intent_orch,
            tool_client=mock_tool_client,
            mongodb=mock_mongodb,
        )

    @pytest.mark.asyncio
    async def test_successful_task_creation(
        self, usecase, mock_intent_orch, mock_tool_client
    ):
        """Test successful task creation flow."""
        # Setup intent parsing result
        intent_result = IntentParseResult(
            title="Buy milk",
            description="Get 2 liters",
            deadline_iso="2025-12-01T15:00:00Z",
            priority="high",
            tags=["shopping"],
            needs_clarification=False,
            questions=[],
        )
        mock_intent_orch.parse_task_intent.return_value = intent_result

        # Setup MCP tool response
        mock_tool_client.call_tool.return_value = {
            "task_id": "507f1f77bcf86cd799439011",
            "status": "created",
            "created_at": "2025-01-01T12:00:00Z",
        }

        # Execute
        result = await usecase.execute(user_id=123, message="Buy milk tomorrow")

        # Verify
        assert result.created is True
        assert result.task_id == "507f1f77bcf86cd799439011"
        assert result.clarification is None
        assert result.error is None
        assert result.intent_payload is None
        mock_intent_orch.parse_task_intent.assert_called_once()
        mock_tool_client.call_tool.assert_called_once_with(
            "add_task",
            {
                "user_id": 123,
                "title": "Buy milk",
                "description": "Get 2 liters",
                "deadline": "2025-12-01T15:00:00Z",
                "priority": "high",
                "tags": ["shopping"],
            },
        )

    @pytest.mark.asyncio
    async def test_clarification_needed(
        self, usecase, mock_intent_orch, mock_tool_client
    ):
        """Test clarification flow when intent needs more info."""
        # Setup intent parsing result with clarification needed
        intent_result = IntentParseResult(
            title="Buy milk",
            description=None,
            deadline_iso=None,
            priority="medium",
            tags=[],
            needs_clarification=True,
            questions=["What is the deadline?"],
        )
        mock_intent_orch.parse_task_intent.return_value = intent_result

        # Execute
        result = await usecase.execute(user_id=123, message="Buy milk")

        # Verify
        assert result.created is False
        assert result.clarification == "What is the deadline?"
        assert result.task_id is None
        assert result.error is None
        assert result.intent_payload is not None
        assert result.intent_payload["title"] == "Buy milk"
        mock_intent_orch.parse_task_intent.assert_called_once()
        mock_tool_client.call_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_intent_parsing_error(
        self, usecase, mock_intent_orch, mock_tool_client
    ):
        """Test error handling when intent parsing fails."""
        # Setup intent parsing to raise exception
        mock_intent_orch.parse_task_intent.side_effect = Exception("Parsing failed")

        # Execute
        result = await usecase.execute(user_id=123, message="Buy milk")

        # Verify
        assert result.created is False
        assert result.task_id is None
        assert result.clarification is None
        assert result.error is not None
        assert "Parsing failed" in result.error
        mock_tool_client.call_tool.assert_not_called()

    @pytest.mark.asyncio
    async def test_mcp_tool_error(self, usecase, mock_intent_orch, mock_tool_client):
        """Test error handling when MCP tool call fails."""
        # Setup intent parsing result
        intent_result = IntentParseResult(
            title="Buy milk",
            description="",
            deadline_iso=None,
            priority="medium",
            tags=[],
            needs_clarification=False,
            questions=[],
        )
        mock_intent_orch.parse_task_intent.return_value = intent_result

        # Setup MCP tool to raise exception
        mock_tool_client.call_tool.side_effect = Exception("MCP error")

        # Execute
        result = await usecase.execute(user_id=123, message="Buy milk")

        # Verify
        assert result.created is False
        assert result.task_id is None
        assert result.error is not None
        assert "MCP error" in result.error
        mock_tool_client.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_tool_error_response(
        self, usecase, mock_intent_orch, mock_tool_client
    ):
        """Test error handling when MCP returns error status."""
        # Setup intent parsing result
        intent_result = IntentParseResult(
            title="Buy milk",
            description="",
            deadline_iso=None,
            priority="medium",
            tags=[],
            needs_clarification=False,
            questions=[],
        )
        mock_intent_orch.parse_task_intent.return_value = intent_result

        # Setup MCP tool to return error response
        mock_tool_client.call_tool.return_value = {
            "status": "error",
            "error": "Validation failed",
        }

        # Execute
        result = await usecase.execute(user_id=123, message="Buy milk")

        # Verify
        assert result.created is False
        assert result.error is not None
        assert "Validation failed" in result.error

    @pytest.mark.asyncio
    async def test_context_passed_to_intent_orch(
        self, usecase, mock_intent_orch, mock_tool_client
    ):
        """Test that context is properly passed to intent orchestrator."""
        intent_result = IntentParseResult(
            title="Buy milk",
            description="",
            deadline_iso=None,
            priority="medium",
            tags=[],
            needs_clarification=False,
            questions=[],
        )
        mock_intent_orch.parse_task_intent.return_value = intent_result
        mock_tool_client.call_tool.return_value = {
            "task_id": "507f1f77bcf86cd799439011",
            "status": "created",
        }

        context = {"previous_message": "Create a task"}
        await usecase.execute(user_id=123, message="Buy milk", context=context)

        mock_intent_orch.parse_task_intent.assert_called_once_with("Buy milk", context)
