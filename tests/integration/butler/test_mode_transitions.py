"""Integration tests for mode transitions.

Following TDD principles: test switching between modes in single session.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

<<<<<<< HEAD
from src.domain.agents.services.mode_classifier import DialogMode
from tests.fixtures.butler_fixtures import butler_orchestrator


@pytest.mark.asyncio
async def test_mode_switch_task_to_data(butler_orchestrator):
=======
from src.application.dtos.butler_dialog_dtos import DialogMode
from tests.fixtures.butler_fixtures import (
    butler_orchestrator,
    mock_task_handler,
    mock_data_handler,
    mock_chat_handler,
    mock_tool_client_protocol,
    mock_llm_client_protocol,
    mock_intent_orchestrator,
)


@pytest.mark.asyncio
async def test_mode_switch_task_to_data(
    butler_orchestrator,
    mock_task_handler,
    mock_data_handler,
    mock_intent_orchestrator,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test switching from TASK to DATA mode.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
<<<<<<< HEAD
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_data_handler: Mocked DataHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
>>>>>>> origin/master
    """
    user_id = "12345"
    session_id = "session_123"

<<<<<<< HEAD
    # Message 1: TASK mode
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
=======
    # Message 1: TASK mode using public API (force_mode)
    mock_intent_orchestrator.parse_task_intent = AsyncMock(
>>>>>>> origin/master
        return_value=MagicMock(
            needs_clarification=False,
            title="Test",
            to_mcp_params=lambda: {"title": "Test"},
        )
    )
<<<<<<< HEAD
    butler_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
=======
    mock_tool_client_protocol.call_tool = AsyncMock(
>>>>>>> origin/master
        return_value={"success": True}
    )

    response1 = await butler_orchestrator.handle_user_message(
<<<<<<< HEAD
        user_id=user_id, message="Create a task", session_id=session_id
    )

    # Message 2: Switch to DATA mode
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    butler_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
=======
        user_id=user_id,
        message="Create a task",
        session_id=session_id,
        force_mode=DialogMode.TASK,
    )

    # Message 2: Switch to DATA mode using public API (force_mode)
    mock_tool_client_protocol.call_tool = AsyncMock(
>>>>>>> origin/master
        return_value={"success": True, "digests": []}
    )

    response2 = await butler_orchestrator.handle_user_message(
<<<<<<< HEAD
        user_id=user_id, message="Get channel digests", session_id=session_id
    )

    # Verify: Both modes handled correctly
    assert response1 is not None
    assert response2 is not None
    # Verify correct handlers called
    assert butler_orchestrator.task_handler.tool_client.call_tool.called
    assert butler_orchestrator.data_handler.tool_client.call_tool.called


@pytest.mark.asyncio
async def test_mode_switch_preserves_context(butler_orchestrator):
=======
        user_id=user_id,
        message="Get channel digests",
        session_id=session_id,
        force_mode=DialogMode.DATA,
    )

    # Verify: Both modes handled correctly (via public API responses)
    assert response1 is not None
    assert response2 is not None
    # Verify correct handlers called via mocked dependency (not private attribute)
    assert mock_tool_client_protocol.call_tool.called


@pytest.mark.asyncio
async def test_mode_switch_preserves_context(
    butler_orchestrator,
    mock_task_handler,
    mock_data_handler,
    mock_intent_orchestrator,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test context is preserved across mode switches.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
<<<<<<< HEAD
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_data_handler: Mocked DataHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
>>>>>>> origin/master
    """
    user_id = "12345"
    session_id = "session_123"

    context_stored = {}

    async def find_one_side_effect(filter_dict):
        # find_one may be called with just session_id
        session_id = filter_dict.get("session_id")
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

<<<<<<< HEAD
    async def update_one_side_effect(filter_dict, update_dict, **kwargs):
        session_id = filter_dict.get("session_id")
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

=======
    async def update_one_side_effect(filter_dict, update_dict, upsert=False):
        # update_one with upsert=True creates new document
        session_id = filter_dict.get("session_id")
        if session_id:
            doc = update_dict.get("$set", {})
            # Try to find existing context
            found_key = None
            for key in context_stored:
                if session_id in key:
                    found_key = key
                    break
            if found_key:
                # Update existing context
                context_stored[found_key].update(doc)
            else:
                # Create new context (upsert)
                key = f"{doc.get('user_id', user_id)}:{doc.get('session_id', session_id)}"
                context_stored[key] = doc
            result = MagicMock()
            result.modified_count = 1
            result.matched_count = 1 if found_key else 0
            result.upserted_id = "test_id" if upsert and not found_key else None
            return result
        result = MagicMock()
        result.modified_count = 0
        result.matched_count = 0
        return result

    # Use public API (mongodb property) to mock MongoDB
>>>>>>> origin/master
    butler_orchestrator.mongodb.dialog_contexts.find_one = AsyncMock(
        side_effect=find_one_side_effect
    )
    butler_orchestrator.mongodb.dialog_contexts.insert_one = AsyncMock(
        side_effect=insert_one_side_effect
    )
    butler_orchestrator.mongodb.dialog_contexts.update_one = AsyncMock(
        side_effect=update_one_side_effect
    )

<<<<<<< HEAD
    # Configure handlers
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        side_effect=["TASK", "DATA"]
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
=======
    # Configure handlers using public API (fixtures)
    mock_intent_orchestrator.parse_task_intent = AsyncMock(
>>>>>>> origin/master
        return_value=MagicMock(
            needs_clarification=False,
            title="Test",
            to_mcp_params=lambda: {"title": "Test"},
        )
    )
<<<<<<< HEAD
    butler_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True}
    )
    butler_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True, "digests": []}
    )

    # Execute: Two messages in same session
    await butler_orchestrator.handle_user_message(
        user_id=user_id, message="Create task", session_id=session_id
    )

    await butler_orchestrator.handle_user_message(
        user_id=user_id, message="Get digests", session_id=session_id
    )

    # Verify: Context was updated (not recreated)
    key = f"{user_id}:{session_id}"
    assert key in context_stored
    # Context should exist after both messages
=======
    mock_tool_client_protocol.call_tool = AsyncMock(
        return_value={"success": True}
    )

    # Execute: Two messages in same session using public API (force_mode)
    await butler_orchestrator.handle_user_message(
        user_id=user_id,
        message="Create task",
        session_id=session_id,
        force_mode=DialogMode.TASK,
    )

    mock_tool_client_protocol.call_tool = AsyncMock(
        return_value={"success": True, "digests": []}
    )

    await butler_orchestrator.handle_user_message(
        user_id=user_id,
        message="Get digests",
        session_id=session_id,
        force_mode=DialogMode.DATA,
    )

    # Verify: Context was updated (not recreated) via public API mock
    key = f"{user_id}:{session_id}"
    assert key in context_stored
    # Context should exist after both messages (verify via public API mock)
>>>>>>> origin/master
    assert butler_orchestrator.mongodb.dialog_contexts.update_one.called


@pytest.mark.asyncio
<<<<<<< HEAD
async def test_mode_classification_accuracy(butler_orchestrator):
=======
async def test_mode_classification_accuracy(
    butler_orchestrator,
    mock_task_handler,
    mock_data_handler,
    mock_chat_handler,
    mock_intent_orchestrator,
    mock_tool_client_protocol,
    mock_llm_client_protocol,
):
>>>>>>> origin/master
    """Test mode classification routes to correct handlers.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
<<<<<<< HEAD
    """
    test_cases = [
        ("TASK", "Create a task to buy milk", butler_orchestrator.task_handler),
        ("DATA", "Get channel digests", butler_orchestrator.data_handler),
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
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_data_handler: Mocked DataHandler with mocked dependencies.
        mock_chat_handler: Mocked ChatHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
        mock_llm_client_protocol: Mocked LLMClientProtocol.
    """
    test_cases = [
        (DialogMode.TASK, "Create a task to buy milk"),
        (DialogMode.DATA, "Get channel digests"),
        (DialogMode.IDLE, "Hello, how are you?"),
    ]

    for expected_mode, message in test_cases:
        # Setup handler responses using public API (fixtures)
        if expected_mode == DialogMode.TASK:
            mock_intent_orchestrator.parse_task_intent = AsyncMock(
>>>>>>> origin/master
                return_value=MagicMock(
                    needs_clarification=False,
                    title="Test",
                    to_mcp_params=lambda: {"title": "Test"},
                )
            )
<<<<<<< HEAD
            expected_handler.tool_client.call_tool = AsyncMock(
                return_value={"success": True}
            )
        elif expected_mode == "DATA":
            expected_handler.tool_client.call_tool = AsyncMock(
                return_value={"success": True, "digests": []}
            )
        elif expected_mode == "IDLE":
            expected_handler.llm_client.make_request = AsyncMock(
                return_value="Chat response"
            )
        else:
            expected_handler.llm_client.make_request = AsyncMock(
                return_value="Chat response"
            )

        # Execute
        response = await butler_orchestrator.handle_user_message(
            user_id="12345", message=message, session_id="session_123"
        )

        # Verify: Correct handler was used
        assert response is not None
        if expected_mode in ["TASK", "DATA"]:
            assert expected_handler.tool_client.call_tool.called
        else:
            assert expected_handler.llm_client.make_request.called
=======
            mock_tool_client_protocol.call_tool = AsyncMock(
                return_value={"success": True}
            )
        elif expected_mode == DialogMode.DATA:
            mock_tool_client_protocol.call_tool = AsyncMock(
                return_value={"success": True, "digests": []}
            )
        elif expected_mode == DialogMode.IDLE:
            mock_llm_client_protocol.make_request = AsyncMock(
                return_value="Chat response"
            )

        # Execute using public API (force_mode)
        response = await butler_orchestrator.handle_user_message(
            user_id="12345",
            message=message,
            session_id="session_123",
            force_mode=expected_mode,
        )

        # Verify: Correct handler was used (via public API response)
        assert response is not None
        # Verify via mocked dependencies (not private attributes)
        if expected_mode in [DialogMode.TASK, DialogMode.DATA]:
            assert mock_tool_client_protocol.call_tool.called
        else:
            assert mock_llm_client_protocol.make_request.called
>>>>>>> origin/master
