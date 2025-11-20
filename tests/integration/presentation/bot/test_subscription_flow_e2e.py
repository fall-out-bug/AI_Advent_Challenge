"""End-to-end integration tests for subscription flow.

Tests full flow from search to subscription with collection.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from src.presentation.bot.handlers.butler_handler import _handle_subscribe_request
from src.presentation.bot.handlers.channels import (
    _handle_subscribe_action,
    handle_channel_search_confirmation,
)


@pytest.fixture
def mock_message():
    """Create mock Telegram message."""
    user = User(id=123, is_bot=False, first_name="Test")
    message = MagicMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    message.message_id = 1
    return message


@pytest.fixture
def mock_state():
    """Create mock FSM state."""
    state = MagicMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={})
    state.set_data = AsyncMock()
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.mark.asyncio
async def test_subscription_flow_with_candidates_cycling(mock_message, mock_state):
    """Test full subscription flow with candidate cycling.

    Purpose:
        Test that user can decline first candidate and see second.
    """
    # Arrange: Mock search results with 3 candidates
    from src.domain.value_objects.channel_resolution import ChannelSearchResult

    candidates = [
        ChannelSearchResult(
            username="channel_1",
            title="Channel 1",
            description="First channel",
            chat_id=1,
        ),
        ChannelSearchResult(
            username="channel_2",
            title="Channel 2",
            description="Second channel",
            chat_id=2,
        ),
        ChannelSearchResult(
            username="channel_3",
            title="Channel 3",
            description="Third channel",
            chat_id=3,
        ),
    ]

    # Mock search use case
    with patch(
        "src.presentation.bot.handlers.butler_handler.SearchChannelForSubscriptionUseCase"
    ) as mock_search_class:
        mock_search_instance = AsyncMock()
        mock_search_instance.execute = AsyncMock(return_value=candidates)
        mock_search_class.return_value = mock_search_instance

        # Mock resolve use case (not found in subscriptions)
        with patch(
            "src.presentation.bot.handlers.butler_handler.ResolveChannelNameUseCase"
        ) as mock_resolve_class:
            mock_resolve_instance = AsyncMock()
            mock_resolve_instance.execute = AsyncMock(
                return_value=MagicMock(
                    found=False,
                    channel_username=None,
                )
            )
            mock_resolve_class.return_value = mock_resolve_instance

            # Act: Handle subscribe request
            await _handle_subscribe_request(
                mock_message, 123, "test_channel", mock_state
            )

    # Assert: First candidate shown
    assert mock_message.answer.called
    call_args = mock_message.answer.call_args[0][0]
    assert "Channel 1" in call_args
    assert "@channel_1" in call_args

    # Assert: State has candidates stored
    set_data_call = mock_state.set_data.call_args[0][0]
    assert "candidates" in set_data_call
    assert len(set_data_call["candidates"]) == 3
    assert set_data_call["cycler_index"] == 0

    # Act: Decline first candidate
    mock_message.text = "нет"
    mock_state.get_data = AsyncMock(
        return_value={
            "candidates": [
                {"username": "channel_1", "title": "Channel 1"},
                {"username": "channel_2", "title": "Channel 2"},
                {"username": "channel_3", "title": "Channel 3"},
            ],
            "cycler_index": 0,
        }
    )
    mock_message.answer.reset_mock()

    await handle_channel_search_confirmation(mock_message, mock_state)

    # Assert: Second candidate shown
    assert mock_message.answer.called
    call_args = mock_message.answer.call_args[0][0]
    assert "Channel 2" in call_args
    assert "@channel_2" in call_args

    # Assert: Index advanced
    update_data_call = mock_state.update_data.call_args[0][0]
    assert update_data_call["cycler_index"] == 1


@pytest.mark.asyncio
async def test_subscription_flow_accept_and_collect(mock_message, mock_state):
    """Test subscription with immediate post collection.

    Purpose:
        Test that after accepting candidate, subscription + collection happens.
    """
    # Arrange: Mock subscribe use case
    from src.application.use_cases.subscribe_with_collection import (
        SubscribeToChannelWithCollectionUseCase,
        SubscribeWithCollectionResult,
    )

    # Create a mock instance that will be returned
    mock_subscribe_instance = AsyncMock()
    mock_subscribe_instance.execute = AsyncMock(
        return_value=SubscribeWithCollectionResult(
            status="subscribed",
            channel_username="onaboka",
            collected_count=5,
        )
    )

    # Patch the import inside _handle_subscribe_action
    # The use case is imported inside the function, so we patch the import path
    with patch(
        "src.application.use_cases.subscribe_with_collection.SubscribeToChannelWithCollectionUseCase",
        return_value=mock_subscribe_instance,
    ) as mock_class:
        mock_state.get_data = AsyncMock(
            return_value={
                "original_message": mock_message,
            }
        )

        # Act: Subscribe
        await _handle_subscribe_action(123, "onaboka", mock_state, mock_message)

    # Assert: Success message with collection count
    assert mock_message.answer.called
    call_args = mock_message.answer.call_args[0][0]
    assert "Подписался" in call_args
    assert "Собрано постов: 5" in call_args
    assert mock_state.clear.called


@pytest.mark.asyncio
async def test_subscription_flow_exhausted_candidates(mock_message, mock_state):
    """Test when all candidates are declined.

    Purpose:
        Test that after declining all candidates, search is cancelled.
    """
    # Arrange: Last candidate
    mock_message.text = "нет"
    mock_state.get_data = AsyncMock(
        return_value={
            "candidates": [
                {"username": "channel_1", "title": "Channel 1"},
                {"username": "channel_2", "title": "Channel 2"},
            ],
            "cycler_index": 1,  # Already at last candidate
        }
    )

    # Act: Decline last candidate
    await handle_channel_search_confirmation(mock_message, mock_state)

    # Assert: Search cancelled
    assert mock_message.answer.called
    call_args = mock_message.answer.call_args[0][0]
    assert "не найден" in call_args.lower()
    assert mock_state.clear.called
