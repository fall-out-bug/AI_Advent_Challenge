"""E2E test fixtures for Telegram bot testing.

Following TDD principles: comprehensive fixtures for end-to-end testing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot, Dispatcher
from aiogram.types import User, Message, Chat

from tests.fixtures.butler_fixtures import butler_orchestrator


@pytest.fixture
def mock_telegram_user():
    """Create mock Telegram user.

    Returns:
        Mock User instance.
    """
    user = MagicMock(spec=User)
    user.id = 12345
    user.username = "test_user"
    user.first_name = "Test"
    user.last_name = "User"
    user.is_bot = False
    return user


@pytest.fixture
def mock_telegram_chat():
    """Create mock Telegram chat.

    Returns:
        Mock Chat instance.
    """
    chat = MagicMock(spec=Chat)
    chat.id = 12345
    chat.type = "private"
    return chat


@pytest.fixture
def mock_telegram_message(mock_telegram_user, mock_telegram_chat):
    """Create mock Telegram message.

    Args:
        mock_telegram_user: Mock Telegram user.
        mock_telegram_chat: Mock Telegram chat.

    Returns:
        Mock Message instance.
    """
    message = MagicMock(spec=Message)
    message.message_id = 123
    message.from_user = mock_telegram_user
    message.chat = mock_telegram_chat
    message.text = "Test message"
    message.answer = AsyncMock()
    return message


@pytest.fixture
async def e2e_orchestrator(butler_orchestrator):
    """ButlerOrchestrator configured for E2E testing.

    Args:
        butler_orchestrator: Base butler orchestrator fixture.

    Returns:
        ButlerOrchestrator for E2E tests.
    """
    return butler_orchestrator


@pytest.fixture
def mock_bot():
    """Create mock aiogram Bot for E2E testing.

    Returns:
        Mock Bot instance.
    """
    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=12345, username="test_bot"))
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    return bot


@pytest.fixture
def mock_dispatcher():
    """Create mock aiogram Dispatcher for E2E testing.

    Returns:
        Mock Dispatcher instance.
    """
    dispatcher = MagicMock(spec=Dispatcher)
    dispatcher.include_router = MagicMock()
    dispatcher.start_polling = AsyncMock()
    dispatcher.stop_polling = AsyncMock()
    dispatcher.feed_update = AsyncMock()
    return dispatcher
