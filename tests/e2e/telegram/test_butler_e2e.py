"""E2E tests for Butler Telegram bot.

Following TDD principles: test complete Telegram bot workflows.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.presentation.bot.butler_bot import ButlerBot
from src.domain.agents.services.mode_classifier import DialogMode
from tests.fixtures.butler_fixtures import butler_orchestrator


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
async def test_task_creation_e2e(e2e_orchestrator, mock_telegram_message):
    """Test complete task creation flow via Telegram.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup: Configure orchestrator for task creation
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    e2e_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=False,
            title="Buy milk",
            description="Tomorrow",
            to_mcp_params=lambda: {"title": "Buy milk", "description": "Tomorrow"}
        )
    )
    e2e_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
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
    
    # Execute: Process message (simulating Telegram update)
    # Note: In real E2E, this would go through aiogram dispatcher
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify: Task created
    assert response is not None
    assert e2e_orchestrator.task_handler.tool_client.call_tool.called


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_task_creation_with_clarification_e2e(e2e_orchestrator, mock_telegram_message):
    """Test task creation with clarification flow.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup: Intent needs clarification
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    e2e_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=True,
            questions=["What is the task title?"]
        )
    )
    
    mock_telegram_message.text = "Create a task"
    
    # Execute
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify: Clarification question asked
    assert response is not None
    assert "?" in response or "title" in response.lower() or "clarification" in response.lower()


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_channel_digest_e2e(e2e_orchestrator, mock_telegram_message):
    """Test channel digest request flow.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup: DATA mode
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    e2e_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
        return_value={
            "success": True,
            "digests": [
                {"channel": "test_channel", "posts": 5}
            ]
        }
    )
    
    mock_telegram_message.text = "Get channel digests"
    
    # Execute
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify: Digests returned
    assert response is not None
    assert e2e_orchestrator.data_handler.tool_client.call_tool.called


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_student_stats_e2e(e2e_orchestrator, mock_telegram_message):
    """Test student stats request flow.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup: DATA mode for stats
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="DATA"
    )
    e2e_orchestrator.data_handler.tool_client.call_tool = AsyncMock(
        return_value={
            "success": True,
            "stats": {
                "total_students": 50,
                "active_students": 45
            }
        }
    )
    
    mock_telegram_message.text = "Get student stats"
    
    # Execute
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify: Stats returned
    assert response is not None
    assert e2e_orchestrator.data_handler.tool_client.call_tool.called


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_reminders_list_e2e(e2e_orchestrator, mock_telegram_message):
    """Test reminders list flow.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup: REMINDERS mode
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="REMINDERS"
    )
    e2e_orchestrator.reminders_handler.tool_client.call_tool = AsyncMock(
        return_value={
            "success": True,
            "reminders": [
                {"id": "rem_1", "text": "Test reminder"}
            ]
        }
    )
    
    mock_telegram_message.text = "Show my reminders"
    
    # Execute
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify: Reminders returned
    assert response is not None
    assert e2e_orchestrator.reminders_handler.tool_client.call_tool.called


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_idle_chat_e2e(e2e_orchestrator, mock_telegram_message):
    """Test IDLE mode general conversation.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup: IDLE mode
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="IDLE"
    )
    e2e_orchestrator.chat_handler.llm_client.make_request = AsyncMock(
        return_value="Hello! How can I help you today?"
    )
    
    mock_telegram_message.text = "Hello, how are you?"
    
    # Execute
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify: LLM response returned
    assert response is not None
    assert "hello" in response.lower() or "help" in response.lower()
    assert e2e_orchestrator.chat_handler.llm_client.make_request.called


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_error_service_unavailable_e2e(e2e_orchestrator, mock_telegram_message):
    """Test error handling when service is unavailable.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup: LLM unavailable
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        side_effect=Exception("LLM unavailable")
    )
    
    mock_telegram_message.text = "Any message"
    
    # Execute: Should not crash
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify: Error handled gracefully
    assert response is not None  # Should return something, even if error message


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_long_message_handling_e2e(e2e_orchestrator, mock_telegram_message):
    """Test handling of long messages.

    Args:
        e2e_orchestrator: ButlerOrchestrator for E2E testing.
        mock_telegram_message: Mock Telegram message.
    """
    # Setup: Long message
    long_message = "Create a task: " + "x" * 5000
    mock_telegram_message.text = long_message
    
    e2e_orchestrator.mode_classifier.llm_client.make_request = AsyncMock(
        return_value="TASK"
    )
    e2e_orchestrator.task_handler.intent_orchestrator.parse_task_intent = AsyncMock(
        return_value=MagicMock(
            needs_clarification=False,
            title="Long task",
            to_mcp_params=lambda: {"title": "Long task"}
        )
    )
    e2e_orchestrator.task_handler.tool_client.call_tool = AsyncMock(
        return_value={"success": True}
    )
    
    # Execute
    response = await e2e_orchestrator.handle_user_message(
        user_id=str(mock_telegram_message.from_user.id),
        message=mock_telegram_message.text,
        session_id=f"{mock_telegram_message.from_user.id}:{mock_telegram_message.message_id}"
    )
    
    # Verify: Long message handled
    assert response is not None

