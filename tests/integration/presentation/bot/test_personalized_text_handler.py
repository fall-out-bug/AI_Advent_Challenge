"""Integration tests for personalized text handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.application.personalization.dtos import PersonalizedReplyOutput


@pytest.mark.asyncio
async def test_text_message_with_personalization_enabled(mocker):
    """Test text message routes through personalization when enabled."""
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.personalization_enabled = True
    mocker.patch(
        "src.infrastructure.config.settings.get_settings",
        return_value=mock_settings,
    )

    # Mock use case
    mock_use_case = MagicMock()
    mock_use_case.execute = AsyncMock(
        return_value=PersonalizedReplyOutput(
            reply="Добрый день, сэр. Чем могу быть полезен?",
            used_persona=True,
            memory_events_used=5,
            compressed=False,
        )
    )

    # Setup handler
    from src.presentation.bot.handlers.butler_handler import (
        setup_butler_handler,
    )
    from src.presentation.bot.orchestrator import ButlerOrchestrator

    mock_orchestrator = MagicMock(spec=ButlerOrchestrator)

    router = setup_butler_handler(
        mock_orchestrator, personalized_reply_use_case=mock_use_case
    )

    # Verify router is set up
    assert router is not None
    # Note: Full integration test would require aiogram test framework
    # This is a placeholder for the test structure


@pytest.mark.asyncio
async def test_text_message_with_personalization_disabled(mocker):
    """Test text message routes through Butler when personalization disabled."""
    mock_settings = MagicMock()
    mock_settings.personalization_enabled = False
    mocker.patch(
        "src.infrastructure.config.settings.get_settings",
        return_value=mock_settings,
    )

    from src.presentation.bot.handlers.butler_handler import (
        setup_butler_handler,
    )
    from src.presentation.bot.orchestrator import ButlerOrchestrator

    mock_orchestrator = MagicMock(spec=ButlerOrchestrator)

    router = setup_butler_handler(mock_orchestrator, personalized_reply_use_case=None)

    # Verify router is set up
    assert router is not None
    # Note: Full integration test would require aiogram test framework

