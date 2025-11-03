"""Integration tests for mode transitions.

Following TDD principles: test switching between modes in single session.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.agents.services.mode_classifier import DialogMode
from tests.fixtures.butler_fixtures import butler_orchestrator


@pytest.mark.asyncio
async def test_mode_switch_task_to_data(butler_orchestrator):
    """Test switching from TASK to DATA mode.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    user_id = "12345"
    session_id = "session_123"
    
    # Message 1: TASK mode
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
    
    response1 = await butler_orchestrator.handle_user_message(
        user_id=user_id,
        message="Create a task",
        session_id=session_id
    )
    
    # Message 2: Switch to DATA mode
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    butler_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True, "digests": []}
    )
    
    response2 = await butler_orchestrator.handle_user_message(
        user_id=user_id,
        message="Get channel digests",
        session_id=session_id
    )
    
    # Verify: Both modes handled correctly
    assert response1 is not None
    assert response2 is not None
    # Verify correct handlers called
    assert butler_orchestrator.task_handler.tool_client.call_tool.called
    assert butler_orchestrator.data_handler.tool_client.call_tool.called


@pytest.mark.asyncio
async def test_mode_switch_preserves_context(butler_orchestrator):
    """Test context is preserved across mode switches.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    user_id = "12345"
    session_id = "session_123"
    
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
    
    async def update_one_side_effect(filter_dict, update_dict, **kwargs):
        session_id = filter_dict.get('session_id')
        if session_id:
            # Find matching context by session_id
            for key in context_stored:
                if session_id in key:
                    context_stored[key].update(update_dict.get("$set", {}))
                    result = MagicMock()
                    result.modified_count = 1
                    return result
        result = MagicMock()
        result.modified_count = 0
        return result
    
    butler_orchestrator.mongodb.dialog_contexts.find_one = AsyncMock(
        side_effect=find_one_side_effect
    )
    butler_orchestrator.mongodb.dialog_contexts.insert_one = AsyncMock(
        side_effect=insert_one_side_effect
    )
    butler_orchestrator.mongodb.dialog_contexts.update_one = AsyncMock(
        side_effect=update_one_side_effect
    )
    
    # Configure handlers
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        side_effect=["TASK", "DATA"]
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
    butler_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True, "digests": []}
    )
    
    # Execute: Two messages in same session
    await butler_orchestrator.handle_user_message(
        user_id=user_id,
        message="Create task",
        session_id=session_id
    )
    
    await butler_orchestrator.handle_user_message(
        user_id=user_id,
        message="Get digests",
        session_id=session_id
    )
    
    # Verify: Context was updated (not recreated)
    key = f"{user_id}:{session_id}"
    assert key in context_stored
    # Context should exist after both messages
    assert butler_orchestrator.mongodb.dialog_contexts.update_one.called


@pytest.mark.asyncio
async def test_mode_classification_accuracy(butler_orchestrator):
    """Test mode classification routes to correct handlers.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
    """
    test_cases = [
        ("TASK", "Create a task to buy milk", butler_orchestrator.task_handler),
        ("DATA", "Get channel digests", butler_orchestrator.data_handler),
        ("REMINDERS", "Show my reminders", butler_orchestrator.reminders_handler),
        ("IDLE", "Hello, how are you?", butler_orchestrator.chat_handler),
    ]
    
    for expected_mode, message, expected_handler in test_cases:
        # Setup mode classifier
        butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
            return_value=expected_mode
        )
        
        # Setup handler responses
        if expected_mode == "TASK":
            expected_handler.intent_orchestrator.parse_task_intent = AsyncMock(
                return_value=MagicMock(
                    needs_clarification=False,
                    title="Test",
                    to_mcp_params=lambda: {"title": "Test"}
                )
            )
            expected_handler.tool_client.call_tool = AsyncMock(
                return_value={"success": True}
            )
        elif expected_mode == "DATA":
            expected_handler.tool_client.call_tool = AsyncMock(
                return_value={"success": True, "digests": []}
            )
        elif expected_mode == "REMINDERS":
            expected_handler.tool_client.call_tool = AsyncMock(
                return_value={"success": True, "reminders": []}
            )
        else:  # IDLE
            expected_handler.llm_client.make_request = AsyncMock(
                return_value="Chat response"
            )
        
        # Execute
        response = await butler_orchestrator.handle_user_message(
            user_id="12345",
            message=message,
            session_id="session_123"
        )
        
        # Verify: Correct handler was used
        assert response is not None
        if expected_mode in ["TASK", "DATA", "REMINDERS"]:
            assert expected_handler.tool_client.call_tool.called
        else:
            assert expected_handler.llm_client.make_request.called

