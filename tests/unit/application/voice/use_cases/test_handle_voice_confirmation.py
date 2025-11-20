"""Unit tests for HandleVoiceConfirmationUseCase.

Purpose:
    Tests voice command confirmation handling: confirm/reject flows,
    Butler integration, and command deletion.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.voice.dtos import HandleVoiceConfirmationInput
from src.application.voice.use_cases.handle_voice_confirmation import (
    HandleVoiceConfirmationUseCase,
)
from src.domain.voice.exceptions import InvalidVoiceCommandError
from src.domain.voice.value_objects import (
    TranscriptionResult,
    VoiceCommand,
    VoiceCommandState,
)
from src.infrastructure.config.settings import Settings


@pytest.fixture
def mock_command_store() -> AsyncMock:
    """Mock voice command store."""
    store = AsyncMock()
    store.get = AsyncMock()
    store.delete = AsyncMock()
    return store


@pytest.fixture
def mock_butler_gateway() -> AsyncMock:
    """Mock Butler gateway."""
    gateway = AsyncMock()
    gateway.handle_user_message = AsyncMock(
        return_value="Дайджест по каналу onaboka..."
    )
    return gateway


@pytest.fixture
def mock_confirmation_gateway() -> AsyncMock:
    """Mock confirmation gateway."""
    gateway = AsyncMock()
    gateway.send_confirmation = AsyncMock()
    return gateway


@pytest.fixture
def mock_settings() -> Settings:
    """Mock settings."""
    settings = MagicMock(spec=Settings)
    return settings


@pytest.fixture
def use_case(
    mock_command_store: AsyncMock,
    mock_butler_gateway: AsyncMock,
    mock_confirmation_gateway: AsyncMock,
    mock_settings: Settings,
) -> HandleVoiceConfirmationUseCase:
    """Create use case with mocked dependencies."""
    return HandleVoiceConfirmationUseCase(
        command_store=mock_command_store,
        butler_gateway=mock_butler_gateway,
        confirmation_gateway=mock_confirmation_gateway,
        settings=mock_settings,
    )


@pytest.fixture
def sample_command() -> VoiceCommand:
    """Sample voice command for testing."""
    command_id = uuid4()
    transcription = TranscriptionResult(
        text="Сделай дайджест по каналу onaboka за последние 24 часа",
        confidence=0.85,
        language="ru",
        duration_ms=3000,
    )
    return VoiceCommand(
        id=command_id,
        user_id="123456789",
        transcription=transcription,
        state=VoiceCommandState.PENDING,
    )


class TestHandleVoiceConfirmationUseCase:
    """Test HandleVoiceConfirmationUseCase."""

    async def test_execute_confirm_success(
        self,
        use_case: HandleVoiceConfirmationUseCase,
        mock_command_store: AsyncMock,
        mock_butler_gateway: AsyncMock,
        sample_command: VoiceCommand,
    ) -> None:
        """Successfully confirm voice command."""
        mock_command_store.get = AsyncMock(return_value=sample_command)

        input_data = HandleVoiceConfirmationInput(
            command_id=sample_command.id,
            user_id="123456789",
            action="confirm",
        )

        response = await use_case.execute(input_data)

        assert response == "Дайджест по каналу onaboka..."

        # Verify command retrieved
        mock_command_store.get.assert_called_once_with(sample_command.id)

        # Verify Butler gateway called with correct session_id
        mock_butler_gateway.handle_user_message.assert_called_once_with(
            user_id="123456789",
            text="Сделай дайджест по каналу onaboka за последние 24 часа",
            session_id=f"voice_123456789_{sample_command.id}",
        )

        # Verify command deleted after confirmation
        mock_command_store.delete.assert_called_once_with(sample_command.id)

    async def test_execute_reject_success(
        self,
        use_case: HandleVoiceConfirmationUseCase,
        mock_command_store: AsyncMock,
        sample_command: VoiceCommand,
    ) -> None:
        """Successfully reject voice command."""
        mock_command_store.get = AsyncMock(return_value=sample_command)

        input_data = HandleVoiceConfirmationInput(
            command_id=sample_command.id,
            user_id="123456789",
            action="reject",
        )

        response = await use_case.execute(input_data)

        assert response == "Команда отклонена. Запишите голос заново."

        # Verify command retrieved
        mock_command_store.get.assert_called_once_with(sample_command.id)

        # Verify Butler gateway not called
        use_case.butler_gateway.handle_user_message.assert_not_called()

        # Verify command deleted after rejection
        mock_command_store.delete.assert_called_once_with(sample_command.id)

    async def test_execute_command_not_found(
        self,
        use_case: HandleVoiceConfirmationUseCase,
        mock_command_store: AsyncMock,
    ) -> None:
        """Handle command not found."""
        command_id = uuid4()
        mock_command_store.get = AsyncMock(return_value=None)

        input_data = HandleVoiceConfirmationInput(
            command_id=command_id,
            user_id="123456789",
            action="confirm",
        )

        with pytest.raises(InvalidVoiceCommandError) as exc_info:
            await use_case.execute(input_data)

        assert str(command_id) in str(exc_info.value.command_id)

    async def test_execute_user_id_mismatch(
        self,
        use_case: HandleVoiceConfirmationUseCase,
        mock_command_store: AsyncMock,
        sample_command: VoiceCommand,
    ) -> None:
        """Handle user ID mismatch."""
        mock_command_store.get = AsyncMock(return_value=sample_command)

        input_data = HandleVoiceConfirmationInput(
            command_id=sample_command.id,
            user_id="999999999",  # Different user ID
            action="confirm",
        )

        with pytest.raises(InvalidVoiceCommandError):
            await use_case.execute(input_data)

        # Verify Butler gateway not called
        use_case.butler_gateway.handle_user_message.assert_not_called()

    async def test_execute_command_already_confirmed(
        self,
        use_case: HandleVoiceConfirmationUseCase,
        mock_command_store: AsyncMock,
        sample_command: VoiceCommand,
    ) -> None:
        """Handle command already confirmed."""
        sample_command.confirm()  # Mark as confirmed
        mock_command_store.get = AsyncMock(return_value=sample_command)

        input_data = HandleVoiceConfirmationInput(
            command_id=sample_command.id,
            user_id="123456789",
            action="confirm",
        )

        # Should raise error because command is already confirmed
        with pytest.raises(InvalidVoiceCommandError):
            await use_case.execute(input_data)

    async def test_execute_butler_gateway_error(
        self,
        use_case: HandleVoiceConfirmationUseCase,
        mock_command_store: AsyncMock,
        mock_butler_gateway: AsyncMock,
        sample_command: VoiceCommand,
    ) -> None:
        """Handle Butler gateway error."""
        mock_command_store.get = AsyncMock(return_value=sample_command)
        mock_butler_gateway.handle_user_message = AsyncMock(
            side_effect=Exception("Butler error")
        )

        input_data = HandleVoiceConfirmationInput(
            command_id=sample_command.id,
            user_id="123456789",
            action="confirm",
        )

        with pytest.raises(RuntimeError, match="Failed to process voice command"):
            await use_case.execute(input_data)
