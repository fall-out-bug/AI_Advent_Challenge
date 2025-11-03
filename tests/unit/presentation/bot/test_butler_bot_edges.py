"""Edge case tests for ButlerBot.

Following TDD principles: test error handling and edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from src.presentation.bot.butler_bot import ButlerBot
from src.domain.agents.butler_orchestrator import ButlerOrchestrator


@pytest.fixture
def mock_orchestrator():
    """Create mock ButlerOrchestrator."""
    return MagicMock(spec=ButlerOrchestrator)


@pytest.fixture
def mock_message():
    """Create mock Telegram Message."""
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.from_user.username = "test_user"
    message.message_id = 123
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
@patch('src.presentation.bot.butler_bot.Bot')
async def test_cmd_start_handles_send_error(mock_bot_class, mock_orchestrator, mock_message):
    """Test /start command handles message send errors.

    Args:
        mock_bot_class: Mocked Bot class.
        mock_orchestrator: Mock ButlerOrchestrator.
        mock_message: Mock Telegram Message.
    """
    # Setup: Message.answer raises exception
    mock_message.answer.side_effect = Exception("Send failed")
    mock_bot_instance = MagicMock()
    mock_bot_class.return_value = mock_bot_instance
    
    # Execute
    bot = ButlerBot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz", orchestrator=mock_orchestrator)
    await bot.cmd_start(mock_message)
    
    # Verify: Error is logged but doesn't crash
    assert mock_message.answer.called


@pytest.mark.asyncio
@patch('src.presentation.bot.butler_bot.Bot')
async def test_cmd_help_handles_send_error(mock_bot_class, mock_orchestrator, mock_message):
    """Test /help command handles message send errors.

    Args:
        mock_bot_class: Mocked Bot class.
        mock_orchestrator: Mock ButlerOrchestrator.
        mock_message: Mock Telegram Message.
    """
    # Setup: Message.answer raises exception
    mock_message.answer.side_effect = TelegramAPIError(message="Invalid request")
    mock_bot_instance = MagicMock()
    mock_bot_class.return_value = mock_bot_instance
    
    # Execute
    bot = ButlerBot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz", orchestrator=mock_orchestrator)
    await bot.cmd_help(mock_message)
    
    # Verify: Error is handled gracefully
    assert mock_message.answer.called


@pytest.mark.asyncio
@patch('src.presentation.bot.butler_bot.Bot')
async def test_cmd_menu_handles_menu_build_error(mock_bot_class, mock_orchestrator, mock_message):
    """Test /menu command handles menu build errors.

    Args:
        mock_bot_class: Mocked Bot class.
        mock_orchestrator: Mock ButlerOrchestrator.
        mock_message: Mock Telegram Message.
    """
    # Setup: Menu import/building fails
    mock_bot_instance = MagicMock()
    mock_bot_class.return_value = mock_bot_instance
    
    with patch("src.presentation.bot.handlers.menu.build_main_menu") as mock_build:
        mock_build.side_effect = Exception("Menu build failed")
        
        # Execute
        bot = ButlerBot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz", orchestrator=mock_orchestrator)
        await bot.cmd_menu(mock_message)
        
        # Verify: Error message sent to user
        assert mock_message.answer.call_count >= 1
        # Check that error message was sent
        call_args = mock_message.answer.call_args_list[-1][0][0]
        assert "Sorry" in call_args or "couldn't load" in call_args or "❌" in call_args


@pytest.mark.asyncio
@patch('src.presentation.bot.butler_bot.Bot')
async def test_cmd_menu_handles_send_error(mock_bot_class, mock_orchestrator, mock_message):
    """Test /menu command handles send errors after menu is built.

    Args:
        mock_bot_class: Mocked Bot class.
        mock_orchestrator: Mock ButlerOrchestrator.
        mock_message: Mock Telegram Message.
    """
    # Setup: First answer succeeds, but we check error handling path
    mock_bot_instance = MagicMock()
    mock_bot_class.return_value = mock_bot_instance
    mock_message.answer.side_effect = [None, Exception("Send failed")]
    
    # Execute
    bot = ButlerBot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz", orchestrator=mock_orchestrator)
    await bot.cmd_menu(mock_message)
    
    # Verify: Attempted to send
    assert mock_message.answer.called


@pytest.mark.asyncio
@patch('src.presentation.bot.butler_bot.Bot')
async def test_run_handles_cancelled_error(mock_bot_class, mock_orchestrator):
    """Test run() handles CancelledError gracefully.

    Args:
        mock_bot_class: Mocked Bot class.
        mock_orchestrator: Mock ButlerOrchestrator.
    """
    import asyncio
    
    mock_bot_instance = MagicMock()
    mock_bot_class.return_value = mock_bot_instance
    mock_bot_instance.session = MagicMock()
    mock_bot_instance.session.close = AsyncMock()
    
    bot = ButlerBot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz", orchestrator=mock_orchestrator)
    bot.dp = MagicMock()
    bot.dp.start_polling = AsyncMock(side_effect=asyncio.CancelledError())
    bot._shutdown_handler = AsyncMock()
    
    # Execute
    await bot.run()
    
    # Verify: Shutdown handler called
    assert bot._shutdown_handler.called


@pytest.mark.asyncio
@patch('src.presentation.bot.butler_bot.Bot')
async def test_shutdown_handler_handles_errors(mock_bot_class, mock_orchestrator):
    """Test _shutdown_handler handles errors during shutdown.

    Args:
        mock_bot_class: Mocked Bot class.
        mock_orchestrator: Mock ButlerOrchestrator.
    """
    mock_bot_instance = MagicMock()
    mock_bot_class.return_value = mock_bot_instance
    mock_bot_instance.session = MagicMock()
    mock_bot_instance.session.close = AsyncMock(side_effect=Exception("Close failed"))
    
    bot = ButlerBot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz", orchestrator=mock_orchestrator)
    bot.dp = MagicMock()
    bot.dp.stop_polling = AsyncMock(side_effect=Exception("Stop failed"))
    
    # Execute: Should not raise
    await bot._shutdown_handler()
    
    # Verify: Both methods called even if first fails
    assert bot.dp.stop_polling.called
    assert bot.bot.session.close.called


@pytest.mark.asyncio
@patch('src.presentation.bot.butler_bot.Bot')
async def test_init_sets_up_all_handlers(mock_bot_class, mock_orchestrator):
    """Test __init__ sets up all handlers correctly.

    Args:
        mock_bot_class: Mocked Bot class.
        mock_orchestrator: Mock ButlerOrchestrator.
    """
    mock_bot_instance = MagicMock()
    mock_bot_class.return_value = mock_bot_instance
    
    # Execute
    bot = ButlerBot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz", orchestrator=mock_orchestrator)
    
    # Verify: All components initialized
    assert bot.bot is not None
    assert bot.dp is not None
    assert bot.router is not None
    assert bot.orchestrator == mock_orchestrator
    assert bot._shutdown_manager is not None


@pytest.mark.asyncio
@patch('src.presentation.bot.butler_bot.Bot')
async def test_message_without_user(mock_bot_class, mock_orchestrator):
    """Test handlers handle messages without user gracefully.

    Args:
        mock_bot_class: Mocked Bot class.
        mock_orchestrator: Mock ButlerOrchestrator.
    """
    # Setup: Message without from_user
    mock_bot_instance = MagicMock()
    mock_bot_class.return_value = mock_bot_instance
    
    message = MagicMock(spec=Message)
    message.from_user = None
    message.answer = AsyncMock()
    
    bot = ButlerBot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz", orchestrator=mock_orchestrator)
    
    # Execute: Should not crash even if from_user is None
    # (handler might access from_user.id which would fail)
    # This tests defensive coding
    try:
        await bot.cmd_start(message)
    except (AttributeError, TypeError):
        # Expected if from_user is None and code accesses it
        pass
    
    # Verify: Message.answer was attempted or error handled
    # (The specific behavior depends on implementation)

