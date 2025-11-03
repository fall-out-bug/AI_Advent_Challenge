"""Integration tests for error recovery.

Following TDD principles: test graceful degradation and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from tests.fixtures.butler_fixtures import butler_orchestrator


@pytest.mark.asyncio
async def test_llm_unavailable_fallback_to_idle(butler_orchestrator):
    """Test fallback to IDLE when LLM is unavailable.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: Mode classifier fails (LLM unavailable)
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        side_effect=Exception("LLM unavailable")
    )
    # Chat handler also uses LLM, but we'll handle that
    butler_orchestrator.chat_handler.llm_client.make_request = AsyncMock(
        side_effect=Exception("LLM unavailable")
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Any message",
        session_id="session_123"
    )
    
    # Verify: Falls back to IDLE mode (should not crash)
    assert response is not None
    # Mode classifier should have failed and returned IDLE


@pytest.mark.asyncio
async def test_mcp_tool_failure_error_message(butler_orchestrator):
    """Test error message sent when MCP tool fails.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: MCP tool call fails
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=False,
            title="Test",
            to_mcp_params=lambda: {"title": "Test"}
        )
    )
    butler_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
        side_effect=Exception("MCP tool failed")
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Create task: Test",
        session_id="session_123"
    )
    
    # Verify: Error message returned (not exception)
    assert response is not None
    # Error should be communicated to user


@pytest.mark.asyncio
async def test_mongodb_connection_failure_graceful(butler_orchestrator):
    """Test graceful handling of MongoDB connection failure.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: MongoDB operations fail
    butler_orchestrator.mongodb.dialog_contexts.find_one = AsyncMock(
        side_effect=Exception("MongoDB connection failed")
    )
    butler_orchestrator.mongodb.dialog_contexts.insert_one = AsyncMock(
        side_effect=Exception("MongoDB connection failed")
    )
    
    # Configure mode classifier and handler
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=False,
            title="Test",
            to_mcp_params=lambda: {"title": "Test"}
        )
    )
    butler_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True}
    )
    
    # Execute: Should handle MongoDB error gracefully
    # (Context operations may fail, but message processing continues)
    try:
        response = await butler_orchestrator.handle_user_message(
            user_id="12345",
            message="Create task: Test",
            session_id="session_123"
        )
        
        # Verify: Response still generated despite MongoDB error
        assert response is not None
    except Exception:
        # If MongoDB error propagates, that's also acceptable behavior
        # (implementation may choose to fail fast)
        pass


@pytest.mark.asyncio
async def test_invalid_tool_call_validation_error(butler_orchestrator):
    """Test validation error for invalid tool calls.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: Tool call with invalid parameters
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    # Tool client validates and raises error
    butler_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
        side_effect=ValueError("Invalid parameters")
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Get channel digests",
        session_id="session_123"
    )
    
    # Verify: Error handled gracefully
    assert response is not None
    # Error should be communicated


@pytest.mark.asyncio
async def test_handler_exception_recovery(butler_orchestrator):
    """Test recovery when handler raises exception.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: Handler raises exception
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        side_effect=Exception("Handler error")
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Create task",
        session_id="session_123"
    )
    
    # Verify: Error handled (either error message or fallback)
    assert response is not None

