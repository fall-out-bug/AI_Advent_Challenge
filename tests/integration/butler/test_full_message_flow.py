"""Integration tests for full message flow across layers.

Following TDD principles: test complete workflows from message to response.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

<<<<<<< HEAD
from src.domain.agents.services.mode_classifier import DialogMode
from tests.fixtures.butler_fixtures import butler_orchestrator


@pytest.mark.asyncio
async def test_task_creation_full_flow(butler_orchestrator):
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
async def test_task_creation_full_flow(
    butler_orchestrator,
    mock_task_handler,
    mock_intent_orchestrator,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test complete task creation flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
<<<<<<< HEAD
    """
    # Setup: Configure mocks for task flow
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
    """
    # Setup: Configure mocks for task flow using public API
    # Mock intent orchestrator to return a valid task intent
    mock_intent_orchestrator.parse_task_intent = AsyncMock(
>>>>>>> origin/master
        return_value=MagicMock(
            needs_clarification=False,
            title="Buy milk",
            description="Tomorrow",
            to_mcp_params=lambda: {"title": "Buy milk", "description": "Tomorrow"},
        )
    )
<<<<<<< HEAD
    butler_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True, "id": "task_123"}
    )

    # Execute
=======
    # Mock tool client to return success
    mock_tool_client_protocol.call_tool = AsyncMock(
        return_value={"success": True, "id": "task_123"}
    )

    # Execute: Use force_mode to bypass mode classification (public API)
>>>>>>> origin/master
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Create a task: Buy milk tomorrow",
        session_id="session_123",
<<<<<<< HEAD
    )

    # Verify: Complete flow executed
=======
        force_mode=DialogMode.TASK,
    )

    # Verify: Complete flow executed (check response via public API)
>>>>>>> origin/master
    assert (
        "task" in response.lower()
        or "created" in response.lower()
        or "success" in response.lower()
    )
<<<<<<< HEAD
    butler_orchestrator.task_handler.tool_client.call_tool.assert_called_once()


@pytest.mark.asyncio
async def test_data_collection_full_flow(butler_orchestrator):
=======
    # Verify tool was called via mocked dependency (not via private attribute)
    mock_tool_client_protocol.call_tool.assert_called_once()


@pytest.mark.asyncio
async def test_data_collection_full_flow(
    butler_orchestrator,
    mock_data_handler,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test complete data collection flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
<<<<<<< HEAD
    """
    # Setup: Configure for DATA mode
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    butler_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
=======
        mock_data_handler: Mocked DataHandler with mocked dependencies.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
    """
    # Setup: Configure for DATA mode using public API
    mock_tool_client_protocol.call_tool = AsyncMock(
>>>>>>> origin/master
        return_value={
            "success": True,
            "digests": [{"channel": "test_channel", "posts": 5}],
        }
    )

<<<<<<< HEAD
    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345", message="Get channel digests", session_id="session_123"
    )

    # Verify
    assert response is not None
    butler_orchestrator.data_handler.tool_client.call_tool.assert_called()


@pytest.mark.asyncio
async def test_idle_chat_full_flow(butler_orchestrator):
=======
    # Execute: Use force_mode to bypass mode classification (public API)
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Get channel digests",
        session_id="session_123",
        force_mode=DialogMode.DATA,
    )

    # Verify: Check response via public API
    assert response is not None
    # Verify tool was called via mocked dependency (not via private attribute)
    mock_tool_client_protocol.call_tool.assert_called()


@pytest.mark.asyncio
async def test_idle_chat_full_flow(
    butler_orchestrator,
    mock_chat_handler,
    mock_llm_client_protocol,
):
>>>>>>> origin/master
    """Test complete IDLE/chat flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
<<<<<<< HEAD
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
        user_id="12345", message="Hello, how are you?", session_id="session_123"
    )

    # Verify
    assert response is not None
    assert "hello" in response.lower() or "help" in response.lower()
    butler_orchestrator.chat_handler.llm_client.make_request.assert_called()


@pytest.mark.asyncio
async def test_clarification_flow(butler_orchestrator):
=======
        mock_chat_handler: Mocked ChatHandler with mocked dependencies.
        mock_llm_client_protocol: Mocked LLMClientProtocol.
    """
    # Setup: Configure for IDLE mode using public API
    mock_llm_client_protocol.make_request = AsyncMock(
        return_value="Hello! How can I help you?"
    )

    # Execute: Use force_mode to bypass mode classification (public API)
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Hello, how are you?",
        session_id="session_123",
        force_mode=DialogMode.IDLE,
    )

    # Verify: Check response via public API
    assert response is not None
    assert "hello" in response.lower() or "help" in response.lower()
    # Verify LLM was called via mocked dependency (not via private attribute)
    mock_llm_client_protocol.make_request.assert_called()


@pytest.mark.asyncio
async def test_clarification_flow(
    butler_orchestrator,
    mock_task_handler,
    mock_intent_orchestrator,
):
>>>>>>> origin/master
    """Test task creation with clarification flow.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
<<<<<<< HEAD
    """
    # Setup: Intent needs clarification
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=True, questions=["What is the task title?"]
        )
    )

    # Execute
    response = await butler_orchestrator.handle_user_message(
        user_id="12345", message="Create a task", session_id="session_123"
    )

    # Verify: Clarification question asked
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
    """
    # Setup: Intent needs clarification using public API
    mock_intent_result = MagicMock()
    mock_intent_result.needs_clarification = True
    mock_intent_result.questions = ["What is the task title?"]
    # Mock dict() method to return a dict (not MagicMock) for Pydantic validation
    mock_intent_result.dict = lambda: {}
    mock_intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=mock_intent_result
    )

    # Execute: Use force_mode to bypass mode classification (public API)
    response = await butler_orchestrator.handle_user_message(
        user_id="12345",
        message="Create a task",
        session_id="session_123",
        force_mode=DialogMode.TASK,
    )

    # Verify: Clarification question asked (check response via public API)
>>>>>>> origin/master
    assert (
        "?" in response
        or "title" in response.lower()
        or "clarification" in response.lower()
    )


@pytest.mark.asyncio
<<<<<<< HEAD
async def test_context_persistence(butler_orchestrator):
=======
async def test_context_persistence(
    butler_orchestrator,
    mock_task_handler,
    mock_intent_orchestrator,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test dialog context is persisted across messages.

    Args:
        butler_orchestrator: ButlerOrchestrator with mocked dependencies.
<<<<<<< HEAD
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
>>>>>>> origin/master
    """
    user_id = "12345"
    session_id = "session_123"

    # Setup: MongoDB returns None first (no context), then context after insert
<<<<<<< HEAD
=======
    # Use public API (mongodb property) to mock MongoDB
>>>>>>> origin/master
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

<<<<<<< HEAD
    async def insert_one_side_effect(doc):
        key = f"{doc['user_id']}:{doc['session_id']}"
        context_stored[key] = doc
        result = MagicMock()
        result.inserted_id = "test_id"
=======
    async def update_one_side_effect(filter_dict, update_dict, upsert=False):
        # update_one with upsert=True creates new document
        session_id = filter_dict.get("session_id")
        if session_id:
            doc = update_dict.get("$set", {})
            key = f"{doc.get('user_id', user_id)}:{doc.get('session_id', session_id)}"
            context_stored[key] = doc
        result = MagicMock()
        result.modified_count = 1
        result.matched_count = 1
        result.upserted_id = "test_id" if upsert else None
>>>>>>> origin/master
        return result

    butler_orchestrator.mongodb.dialog_contexts.find_one = AsyncMock(
        side_effect=find_one_side_effect
    )
<<<<<<< HEAD
    butler_orchestrator.mongodb.dialog_contexts.insert_one = AsyncMock(
        side_effect=insert_one_side_effect
    )

    # Configure mode classifier
    butler_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    butler_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
=======
    butler_orchestrator.mongodb.dialog_contexts.update_one = AsyncMock(
        side_effect=update_one_side_effect
    )

    # Configure task handler using public API
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

    # Execute: First message
    await butler_orchestrator.handle_user_message(
        user_id=user_id, message="Create task: Test", session_id=session_id
    )

    # Verify: Context was stored
=======
    mock_tool_client_protocol.call_tool = AsyncMock(return_value={"success": True})

    # Execute: First message using force_mode (public API)
    await butler_orchestrator.handle_user_message(
        user_id=user_id,
        message="Create task: Test",
        session_id=session_id,
        force_mode=DialogMode.TASK,
    )

    # Verify: Context was stored (check via public API mock)
>>>>>>> origin/master
    assert len(context_stored) > 0
    key = f"{user_id}:{session_id}"
    assert key in context_stored
