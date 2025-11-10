"""Unit tests for butler_handler.

Following TDD: Test first, then implementation.
Following Python Zen: Simple is better than complex.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Chat

from src.presentation.bot.handlers.butler_handler import (
    _handle_error,
    _safe_answer,
    handle_any_message,
    setup_butler_handler,
)
from src.presentation.bot.orchestrator import ButlerOrchestrator


@pytest.fixture
def mock_orchestrator():
    """Create mock ButlerOrchestrator."""
    orchestrator = MagicMock(spec=ButlerOrchestrator)
    orchestrator.handle_user_message = AsyncMock(return_value="Test response")
    return orchestrator


@pytest.fixture
def mock_message():
    """Create mock Telegram message."""
    message = MagicMock(spec=Message)
    message.text = "Test message"
    message.message_id = 123
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 456
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_setup_butler_handler(mock_orchestrator):
    """Test setup_butler_handler creates router correctly."""
    router = setup_butler_handler(mock_orchestrator)

    assert router is not None
    assert len(router.message.handlers) > 0


@pytest.mark.asyncio
async def test_handle_any_message_success(mock_orchestrator, mock_message):
    """Test successful message handling."""
    setup_butler_handler(mock_orchestrator)

    await handle_any_message(mock_message)

    mock_orchestrator.handle_user_message.assert_called_once_with(
        user_id="456", message="Test message", session_id="telegram_456_123"
    )
    mock_message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_handle_any_message_no_text(mock_orchestrator):
    """Test handling message without text."""
    setup_butler_handler(mock_orchestrator)

    message = MagicMock(spec=Message)
    message.text = None
    message.from_user = MagicMock()

    await handle_any_message(message)

    mock_orchestrator.handle_user_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_any_message_no_user(mock_orchestrator):
    """Test handling message without user."""
    setup_butler_handler(mock_orchestrator)

    message = MagicMock(spec=Message)
    message.text = "Test"
    message.from_user = None

    await handle_any_message(message)

    mock_orchestrator.handle_user_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_any_message_orchestrator_error(mock_orchestrator, mock_message):
    """Test error handling when orchestrator fails."""
    setup_butler_handler(mock_orchestrator)
    mock_orchestrator.handle_user_message.side_effect = Exception("Test error")

    await handle_any_message(mock_message)

    # Error handler should be called
    assert mock_message.answer.call_count >= 1


@pytest.mark.asyncio
async def test_handle_any_message_no_orchestrator(mock_message):
    """Test handling when orchestrator not initialized."""
    # Set orchestrator to None
    import src.presentation.bot.handlers.butler_handler as handler_module

    original = handler_module._orchestrator
    handler_module._orchestrator = None

    try:
        await handle_any_message(mock_message)
        # Should call error handler
        assert mock_message.answer.call_count >= 1
    finally:
        handler_module._orchestrator = original


@pytest.mark.asyncio
async def test_safe_answer_success(mock_message):
    """Test successful answer sending."""
    await _safe_answer(mock_message, "Test response")

    mock_message.answer.assert_called_once_with("Test response", parse_mode="Markdown")


@pytest.mark.asyncio
async def test_safe_answer_long_message(mock_message):
    """Test answering with long message (truncation)."""
    long_text = "x" * 5000
    await _safe_answer(mock_message, long_text)

    call_args = mock_message.answer.call_args
    assert call_args is not None
    sent_text = call_args[0][0]
    assert len(sent_text) <= 4000
    assert "_(сообщение обрезано)_" in sent_text


@pytest.mark.asyncio
async def test_safe_answer_send_error(mock_message):
    """Test error handling when sending fails."""
    mock_message.answer.side_effect = Exception("Send error")

    # Should not raise exception
    await _safe_answer(mock_message, "Test")


@pytest.mark.asyncio
async def test_handle_error(mock_message):
    """Test error handler sends user-friendly message."""
    await _handle_error(mock_message, Exception("Test error"))

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "error" in call_args.lower() or "❌" in call_args
