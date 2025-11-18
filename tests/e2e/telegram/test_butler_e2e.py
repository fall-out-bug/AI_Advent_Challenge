"""E2E tests for Butler Telegram bot.

Following TDD principles: test complete Telegram bot workflows.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.presentation.bot.butler_bot import ButlerBot
<<<<<<< HEAD
from src.domain.agents.services.mode_classifier import DialogMode
from tests.fixtures.butler_fixtures import butler_orchestrator
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
>>>>>>> origin/master


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_start_command_e2e(e2e_orchestrator, mock_telegram_message):
    """Test /start command workflow.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup
    mock_telegram_message.text = "/start"

    # Create bot
    bot = ButlerBot(token="test_token", orchestrator=e2e_orchestrator)

    # Execute: Call start command handler
    await bot.cmd_start(mock_telegram_message)

    # Verify: Welcome message sent
    assert mock_telegram_message.answer.called
    call_args = mock_telegram_message.answer.call_args[0][0]
    assert "butler" in call_args.lower() or "help" in call_args.lower()


@pytest.mark.asyncio
@pytest.mark.e2e
<<<<<<< HEAD
async def test_task_creation_e2e(e2e_orchestrator, mock_telegram_message):
=======
async def test_task_creation_e2e(
    e2e_orchestrator,
    mock_telegram_message,
    mock_task_handler,
    mock_intent_orchestrator,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test complete task creation flow via Telegram.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
<<<<<<< HEAD
    """
    # Setup: Configure orchestrator for task creation
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    e2e_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
    """
    # Setup: Configure handlers using public API (fixtures)
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
    e2e_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
=======
    mock_tool_client_protocol.call_tool = AsyncMock(
>>>>>>> origin/master
        return_value={"success": True, "id": "task_123"}
    )

    mock_telegram_message.text = "Create a task: Buy milk tomorrow"

    # Create bot and handler
    bot = ButlerBot(token="test_token", orchestrator=e2e_orchestrator)

    # Simulate message processing through butler handler
    from src.presentation.bot.handlers.butler_handler import handle_any_message
    from src.presentation.bot.handlers.butler_handler import setup_butler_handler

    # Setup handler with orchestrator
    handler_router = setup_butler_handler(e2e_orchestrator)

<<<<<<< HEAD
    # Execute: Process message (simulating Telegram update)
=======
    # Execute: Process message using public API (force_mode)
>>>>>>> origin/master
    # Note: In real E2E, this would go through aiogram dispatcher
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}",
<<<<<<< HEAD
    )

    # Verify: Task created
    assert response is not None
    assert e2e_orchestrator.task_handler.tool_client.call_tool.called
=======
        force_mode=DialogMode.TASK,
    )

    # Verify: Task created (via public API response)
    assert response is not None
    # Verify via mocked dependency (not private attribute)
    mock_tool_client_protocol.call_tool.assert_called_once()
>>>>>>> origin/master


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_task_creation_with_clarification_e2e(
<<<<<<< HEAD
    e2e_orchestrator, mock_telegram_message
=======
    e2e_orchestrator,
    mock_telegram_message,
    mock_task_handler,
    mock_intent_orchestrator,
>>>>>>> origin/master
):
    """Test task creation with clarification flow.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
<<<<<<< HEAD
    """
    # Setup: Intent needs clarification
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    e2e_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=True, questions=["What is the task title?"]
        )
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
    """
    # Setup: Intent needs clarification using public API (fixture)
    mock_intent_result = MagicMock()
    mock_intent_result.needs_clarification = True
    mock_intent_result.questions = ["What is the task title?"]
    # Mock dict() method to return a dict (not MagicMock) for Pydantic validation
    mock_intent_result.dict = lambda: {}
    mock_intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=mock_intent_result
>>>>>>> origin/master
    )

    mock_telegram_message.text = "Create a task"

<<<<<<< HEAD
    # Execute
=======
    # Execute using public API (force_mode)
>>>>>>> origin/master
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}",
<<<<<<< HEAD
    )

    # Verify: Clarification question asked
=======
        force_mode=DialogMode.TASK,
    )

    # Verify: Clarification question asked (via public API response)
>>>>>>> origin/master
    assert response is not None
    assert (
        "?" in response
        or "title" in response.lower()
        or "clarification" in response.lower()
    )


@pytest.mark.asyncio
@pytest.mark.e2e
<<<<<<< HEAD
async def test_channel_digest_e2e(e2e_orchestrator, mock_telegram_message):
=======
async def test_channel_digest_e2e(
    e2e_orchestrator,
    mock_telegram_message,
    mock_data_handler,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test channel digest request flow.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
<<<<<<< HEAD
    """
    # Setup: DATA mode
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    e2e_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
=======
        mock_data_handler: Mocked DataHandler with mocked dependencies.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
    """
    # Setup: DATA mode using public API (fixture)
    mock_tool_client_protocol.call_tool = AsyncMock(
>>>>>>> origin/master
        return_value={
            "success": True,
            "digests": [{"channel": "test_channel", "posts": 5}],
        }
    )

    mock_telegram_message.text = "Get channel digests"

<<<<<<< HEAD
    # Execute
=======
    # Execute using public API (force_mode)
>>>>>>> origin/master
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}",
<<<<<<< HEAD
    )

    # Verify: Digests returned
    assert response is not None
    assert e2e_orchestrator.data_handler.tool_client.call_tool.called
=======
        force_mode=DialogMode.DATA,
    )

    # Verify: Digests returned (via public API response)
    assert response is not None
    # Verify via mocked dependency (not private attribute)
    mock_tool_client_protocol.call_tool.assert_called()
>>>>>>> origin/master


@pytest.mark.asyncio
@pytest.mark.e2e
<<<<<<< HEAD
async def test_student_stats_e2e(e2e_orchestrator, mock_telegram_message):
=======
async def test_student_stats_e2e(
    e2e_orchestrator,
    mock_telegram_message,
    mock_data_handler,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test student stats request flow.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
<<<<<<< HEAD
    """
    # Setup: DATA mode for stats
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    e2e_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
=======
        mock_data_handler: Mocked DataHandler with mocked dependencies.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
    """
    # Setup: DATA mode for stats using public API (fixture)
    mock_tool_client_protocol.call_tool = AsyncMock(
>>>>>>> origin/master
        return_value={
            "success": True,
            "stats": {"total_students": 50, "active_students": 45},
        }
    )

    mock_telegram_message.text = "Get student stats"

<<<<<<< HEAD
    # Execute
=======
    # Execute using public API (force_mode)
>>>>>>> origin/master
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}",
<<<<<<< HEAD
    )

    # Verify: Stats returned
    assert response is not None
    assert e2e_orchestrator.data_handler.tool_client.call_tool.called
=======
        force_mode=DialogMode.DATA,
    )

    # Verify: Stats returned (via public API response)
    assert response is not None
    # Verify via mocked dependency (not private attribute)
    mock_tool_client_protocol.call_tool.assert_called()
>>>>>>> origin/master


@pytest.mark.asyncio
@pytest.mark.e2e
<<<<<<< HEAD
async def test_idle_chat_e2e(e2e_orchestrator, mock_telegram_message):
=======
async def test_idle_chat_e2e(
    e2e_orchestrator,
    mock_telegram_message,
    mock_chat_handler,
    mock_llm_client_protocol,
):
>>>>>>> origin/master
    """Test IDLE mode general conversation.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
<<<<<<< HEAD
    """
    # Setup: IDLE mode
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="IDLE"
    )
    e2e_orchestrator.chat_handler.llm_client.make_request = AsyncMock(
=======
        mock_chat_handler: Mocked ChatHandler with mocked dependencies.
        mock_llm_client_protocol: Mocked LLMClientProtocol.
    """
    # Setup: IDLE mode using public API (fixture)
    mock_llm_client_protocol.make_request = AsyncMock(
>>>>>>> origin/master
        return_value="Hello! How can I help you today?"
    )

    mock_telegram_message.text = "Hello, how are you?"

<<<<<<< HEAD
    # Execute
=======
    # Execute using public API (force_mode)
>>>>>>> origin/master
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}",
<<<<<<< HEAD
    )

    # Verify: LLM response returned
    assert response is not None
    assert "hello" in response.lower() or "help" in response.lower()
    assert e2e_orchestrator.chat_handler.llm_client.make_request.called
=======
        force_mode=DialogMode.IDLE,
    )

    # Verify: LLM response returned (via public API response)
    assert response is not None
    assert "hello" in response.lower() or "help" in response.lower()
    # Verify via mocked dependency (not private attribute)
    mock_llm_client_protocol.make_request.assert_called()
>>>>>>> origin/master


@pytest.mark.asyncio
@pytest.mark.e2e
<<<<<<< HEAD
async def test_error_service_unavailable_e2e(e2e_orchestrator, mock_telegram_message):
=======
async def test_error_service_unavailable_e2e(
    e2e_orchestrator,
    mock_telegram_message,
    mock_chat_handler,
    mock_llm_client_protocol,
):
>>>>>>> origin/master
    """Test error handling when service is unavailable.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
<<<<<<< HEAD
    """
    # Setup: LLM unavailable
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
=======
        mock_chat_handler: Mocked ChatHandler with mocked dependencies.
        mock_llm_client_protocol: Mocked LLMClientProtocol.
    """
    # Setup: LLM unavailable using public API (fixture)
    mock_llm_client_protocol.make_request = AsyncMock(
>>>>>>> origin/master
        side_effect=Exception("LLM unavailable")
    )

    mock_telegram_message.text = "Any message"

<<<<<<< HEAD
    # Execute: Should not crash
=======
    # Execute: Should not crash using public API (force_mode)
    # Force IDLE mode to test LLM error handling
>>>>>>> origin/master
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}",
<<<<<<< HEAD
    )

    # Verify: Error handled gracefully
=======
        force_mode=DialogMode.IDLE,
    )

    # Verify: Error handled gracefully via public API
>>>>>>> origin/master
    assert response is not None  # Should return something, even if error message


@pytest.mark.asyncio
@pytest.mark.e2e
<<<<<<< HEAD
async def test_long_message_handling_e2e(e2e_orchestrator, mock_telegram_message):
=======
async def test_long_message_handling_e2e(
    e2e_orchestrator,
    mock_telegram_message,
    mock_task_handler,
    mock_intent_orchestrator,
    mock_tool_client_protocol,
):
>>>>>>> origin/master
    """Test handling of long messages.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
<<<<<<< HEAD
=======
        mock_task_handler: Mocked TaskHandler with mocked dependencies.
        mock_intent_orchestrator: Mocked IntentOrchestrator.
        mock_tool_client_protocol: Mocked ToolClientProtocol.
>>>>>>> origin/master
    """
    # Setup: Long message
    long_message = "Create a task: " + "x" * 5000
    mock_telegram_message.text = long_message

<<<<<<< HEAD
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    e2e_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
=======
    # Setup handlers using public API (fixture)
    mock_intent_orchestrator.parse_task_intent = AsyncMock(
>>>>>>> origin/master
        return_value=MagicMock(
            needs_clarification=False,
            title="Long task",
            to_mcp_params=lambda: {"title": "Long task"},
        )
    )
<<<<<<< HEAD
    e2e_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True}
    )

    # Execute
=======
    mock_tool_client_protocol.call_tool = AsyncMock(
        return_value={"success": True}
    )

    # Execute using public API (force_mode)
>>>>>>> origin/master
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}",
<<<<<<< HEAD
    )

    # Verify: Long message handled
=======
        force_mode=DialogMode.TASK,
    )

    # Verify: Long message handled (via public API response)
>>>>>>> origin/master
    assert response is not None
