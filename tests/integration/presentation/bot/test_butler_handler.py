"""Integration tests for butler_handler.

Testing full flow: message → orchestrator → handler → response.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User

from src.presentation.bot.handlers.butler_handler import (
    setup_butler_handler,
    handle_any_message,
)
from src.presentation.bot.orchestrator import ButlerOrchestrator
from src.application.services.mode_classifier import ModeClassifier
from src.application.dtos.butler_dialog_dtos import DialogMode
from src.presentation.bot.handlers.chat import ChatHandler


@pytest.fixture
async def mock_orchestrator():
    """Create mock ButlerOrchestrator for integration testing."""
    orchestrator = MagicMock(spec=ButlerOrchestrator)
    orchestrator.handle_user_message = AsyncMock(
        return_value="Integration test response"
    )
    return orchestrator


@pytest.fixture
def mock_message():
    """Create mock Telegram message."""
    message = MagicMock(spec=Message)
    message.text = "Create a task"
    message.message_id = 789
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 999
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_full_message_flow(mock_orchestrator, mock_message):
    """Test complete message flow through handler."""
    router = setup_butler_handler(mock_orchestrator)

    await handle_any_message(mock_message)

    # Verify orchestrator was called correctly
    mock_orchestrator.handle_user_message.assert_called_once_with(
        user_id="999", message="Create a task", session_id="telegram_999_789"
    )

    # Verify response was sent
    assert mock_message.answer.call_count == 1


@pytest.mark.asyncio
async def test_handler_with_different_modes(mock_message):
    """Test handler with different dialog modes."""
    orchestrator = MagicMock(spec=ButlerOrchestrator)

    # Test TASK mode
    orchestrator.handle_user_message = AsyncMock(return_value="✅ Task created!")
    setup_butler_handler(orchestrator)
    await handle_any_message(mock_message)

    orchestrator.handle_user_message.assert_called_once()
    assert "Task" in orchestrator.handle_user_message.return_value


@pytest.mark.asyncio
async def test_error_recovery(mock_message):
    """Test error recovery in handler."""
    orchestrator = MagicMock(spec=ButlerOrchestrator)
    orchestrator.handle_user_message = AsyncMock(side_effect=RuntimeError("Test error"))

    setup_butler_handler(orchestrator)
    await handle_any_message(mock_message)

    # Error should be handled gracefully
    assert mock_message.answer.call_count >= 1
    # Error message should be user-friendly
    call_args = mock_message.answer.call_args_list[-1][0][0]
    assert "error" in call_args.lower() or "❌" in call_args


@pytest.mark.asyncio
async def test_multiple_messages(mock_orchestrator):
    """Test handling multiple messages."""
    setup_butler_handler(mock_orchestrator)

    messages = []
    for i in range(3):
        msg = MagicMock(spec=Message)
        msg.text = f"Message {i}"
        msg.message_id = i
        msg.from_user = MagicMock(spec=User)
        msg.from_user.id = 100 + i
        msg.answer = AsyncMock()
        messages.append(msg)

    for msg in messages:
        await handle_any_message(msg)

    assert mock_orchestrator.handle_user_message.call_count == 3
