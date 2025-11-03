"""Integration tests for full message flow across layers.

Following TDD principles: test complete workflows from message to response.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.agents.services.mode_classifier import DialogMode
from tests.fixtures.butler_fixtures import butler_orchestrator


@pytest.mark.asyncio
async def test_task_creation_full_flow(butler_orchestrator):
    """Test complete task creation flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: Configure mocks for task flow
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=False,
            title="Buy milk",
            description="Tomorrow",
            to_mcp_params=lambda: {"title": "Buy milk", "description": "Tomorrow"}
        )
    )
    butler_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True, "id": "task_123"}
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Create a task: Buy milk tomorrow",
        session_id="session_123"
    )
    
    # Verify: Complete flow executed
    assert "task" in response.lower() or "created" in response.lower() or "success" in response.lower()
    butler_orchestrator.task_handler.tool_client.call_tool.assert_called_once()


@pytest.mark.asyncio
async def test_data_collection_full_flow(butler_orchestrator):
    """Test complete data collection flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: Configure for DATA mode
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    butler_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
        return_value={
            "success": True,
            "digests": [
                {"channel": "test_channel", "posts": 5}
            ]
        }
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Get channel digests",
        session_id="session_123"
    )
    
    # Verify
    assert response is not None
    butler_orchestrator.data_handler.tool_client.call_tool.assert_called()


@pytest.mark.asyncio
async def test_reminders_listing_full_flow(butler_orchestrator):
    """Test complete reminders listing flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: Configure for REMINDERS mode
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="REMINDERS"
    )
    butler_orchestrator.reminders_handler.tool_client.call_tool = AsyncMock(
        return_value={
            "success": True,
            "reminders": [
                {"id": "rem_1", "text": "Test reminder"}
            ]
        }
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Show my reminders",
        session_id="session_123"
    )
    
    # Verify
    assert response is not None
    butler_orchestrator.reminders_handler.tool_client.call_tool.assert_called()


@pytest.mark.asyncio
async def test_idle_chat_full_flow(butler_orchestrator):
    """Test complete IDLE/chat flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: Configure for IDLE mode
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="IDLE"
    )
    butler_orchestrator.chat_handler.llm_client.make_request = AsyncMock(
        return_value="Hello! How can I help you?"
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Hello, how are you?",
        session_id="session_123"
    )
    
    # Verify
    assert response is not None
    assert "hello" in response.lower() or "help" in response.lower()
    butler_orchestrator.chat_handler.llm_client.make_request.assert_called()


@pytest.mark.asyncio
async def test_clarification_flow(butler_orchestrator):
    """Test task creation with clarification flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    # Setup: Intent needs clarification
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=True,
            questions=["What is the task title?"]
        )
    )
    
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Create a task",
        session_id="session_123"
    )
    
    # Verify: Clarification question asked
    assert "?" in response or "title" in response.lower() or "clarification" in response.lower()


@pytest.mark.asyncio
async def test_context_persistence(butler_orchestrator):
    """Test dialog context is persisted across messages.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    user_id = "12345"
    session_id = "session_123"
    
    # Setup: MongoDB returns None first (no context), then context after insert
    context_stored = {}
    
    async def find_one_side_effect(filter_dict):
        # find_one may be called with just session_id
        session_id = filter_dict.get('session_id')
        if session_id:
            # Try to find by session_id (may be stored with user_id:session_id key)
            for key, value in context_stored.items():
                if session_id in key:
                    return value
        return None
    
    async def insert_one_side_effect(doc):
        key = f"{doc['user_id']}:{doc['session_id']}"
        context_stored[key] = doc
        result = MagicMock()
        result.inserted_id = "test_id"
        return result
    
    butler_orchestrator.mongodb.dialog_contexts.find_one = AsyncMock(
        side_effect=find_one_side_effect
    )
    butler_orchestrator.mongodb.dialog_contexts.insert_one = AsyncMock(
        side_effect=insert_one_side_effect
    )
    
    # Configure mode classifier
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
    
    # Execute: First message
    await butler_orchestrator.handle_user_message(
        user_id=user_id,
        message="Create task: Test",
        session_id=session_id
    )
    
    # Verify: Context was stored
    assert len(context_stored) > 0
    key = f"{user_id}:{session_id}"
    assert key in context_stored

