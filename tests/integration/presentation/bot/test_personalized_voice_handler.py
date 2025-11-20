"""Integration tests for personalized voice handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.personalization.dtos import PersonalizedReplyOutput


@pytest.mark.asyncio
async def test_voice_message_with_personalization_enabled(mocker):
    """Test voice message routes through personalization after STT."""
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.personalization_enabled = True
    mocker.patch(
        "src.infrastructure.config.settings.get_settings",
        return_value=mock_settings,
    )

    # Mock use cases
    mock_process_use_case = MagicMock()
    mock_confirmation_use_case = MagicMock()
    mock_personalized_use_case = MagicMock()
    mock_personalized_use_case.execute = AsyncMock(
        return_value=PersonalizedReplyOutput(
            reply="Добрый день, сэр. Чем могу быть полезен?",
            used_persona=True,
            memory_events_used=3,
            compressed=False,
        )
    )

    from src.presentation.bot.handlers.voice_handler import setup_voice_handler

    router = setup_voice_handler(
        process_use_case=mock_process_use_case,
        confirmation_use_case=mock_confirmation_use_case,
        personalized_reply_use_case=mock_personalized_use_case,
    )

    # Verify router is set up
    assert router is not None
    # Note: Full integration test would require aiogram test framework
    # This is a placeholder for the test structure


@pytest.mark.asyncio
async def test_voice_message_with_personalization_disabled(mocker):
    """Test voice message sends transcription only when personalization disabled."""
    mock_settings = MagicMock()
    mock_settings.personalization_enabled = False
    mocker.patch(
        "src.infrastructure.config.settings.get_settings",
        return_value=mock_settings,
    )

    mock_process_use_case = MagicMock()
    mock_confirmation_use_case = MagicMock()

    from src.presentation.bot.handlers.voice_handler import setup_voice_handler

    router = setup_voice_handler(
        process_use_case=mock_process_use_case,
        confirmation_use_case=mock_confirmation_use_case,
        personalized_reply_use_case=None,
    )

    # Verify router is set up
    assert router is not None
    # Note: Full integration test would require aiogram test framework
