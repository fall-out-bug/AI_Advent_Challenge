"""Unit tests for ProcessVoiceCommandUseCase.

Purpose:
    Tests voice command processing: validation, STT, confidence check,
    storage, and confirmation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.voice.dtos import ProcessVoiceCommandInput
from src.application.voice.use_cases.process_voice_command import (
    ProcessVoiceCommandUseCase,
)
from src.domain.voice.exceptions import SpeechToTextError
from src.domain.voice.value_objects import TranscriptionResult
from src.infrastructure.config.settings import Settings


@pytest.fixture
def mock_stt_service() -> AsyncMock:
    """Mock STT service."""
    service = AsyncMock()
    service.transcribe = AsyncMock(
        return_value=TranscriptionResult(
            text="Сделай дайджест по каналу X",
            confidence=0.85,
            language="ru",
            duration_ms=3000,
        )
    )
    return service


@pytest.fixture
def mock_command_store() -> AsyncMock:
    """Mock voice command store."""
    store = AsyncMock()
    store.save = AsyncMock()
    return store


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
    settings.stt_min_confidence = 0.6
    settings.voice_command_ttl_seconds = 600
    return settings


@pytest.fixture
def use_case(
    mock_stt_service: AsyncMock,
    mock_command_store: AsyncMock,
    mock_confirmation_gateway: AsyncMock,
    mock_settings: Settings,
) -> ProcessVoiceCommandUseCase:
    """Create use case with mocked dependencies."""
    return ProcessVoiceCommandUseCase(
        stt_service=mock_stt_service,
        command_store=mock_command_store,
        confirmation_gateway=mock_confirmation_gateway,
        settings=mock_settings,
    )


class TestProcessVoiceCommandUseCase:
    """Test ProcessVoiceCommandUseCase."""

    async def test_execute_success(
        self,
        use_case: ProcessVoiceCommandUseCase,
        mock_stt_service: AsyncMock,
        mock_command_store: AsyncMock,
        mock_confirmation_gateway: AsyncMock,
    ) -> None:
        """Successfully process voice command."""
        command_id = uuid4()
        input_data = ProcessVoiceCommandInput(
            command_id=command_id,
            user_id="123456789",
            audio_bytes=b"audio data",
            duration_seconds=3.5,
        )

        result = await use_case.execute(input_data)

        assert result.text == "Сделай дайджест по каналу X"
        assert result.confidence == 0.85

        # Verify STT service called
        mock_stt_service.transcribe.assert_called_once_with(
            audio=b"audio data",
            language="ru",
        )

        # Verify command stored
        mock_command_store.save.assert_called_once()
        saved_command = mock_command_store.save.call_args[0][0]
        assert saved_command.id == command_id
        assert saved_command.user_id == "123456789"

        # Verify confirmation sent
        mock_confirmation_gateway.send_confirmation.assert_called_once_with(
            user_id="123456789",
            text="Сделай дайджест по каналу X",
            command_id=command_id,
        )

    async def test_execute_stt_error(
        self,
        use_case: ProcessVoiceCommandUseCase,
        mock_stt_service: AsyncMock,
    ) -> None:
        """Handle STT transcription error."""
        command_id = uuid4()
        input_data = ProcessVoiceCommandInput(
            command_id=command_id,
            user_id="123456789",
            audio_bytes=b"audio data",
            duration_seconds=3.5,
        )

        mock_stt_service.transcribe = AsyncMock(
            side_effect=SpeechToTextError("STT failed", audio_format="wav")
        )

        with pytest.raises(SpeechToTextError):
            await use_case.execute(input_data)

        # Verify command not stored
        use_case.command_store.save.assert_not_called()

        # Verify confirmation not sent
        use_case.confirmation_gateway.send_confirmation.assert_not_called()

    async def test_execute_low_confidence(
        self,
        use_case: ProcessVoiceCommandUseCase,
        mock_stt_service: AsyncMock,
        mock_settings: Settings,
    ) -> None:
        """Handle low confidence transcription."""
        command_id = uuid4()
        input_data = ProcessVoiceCommandInput(
            command_id=command_id,
            user_id="123456789",
            audio_bytes=b"audio data",
            duration_seconds=3.5,
        )

        # Set confidence below threshold
        mock_stt_service.transcribe = AsyncMock(
            return_value=TranscriptionResult(
                text="Some text",
                confidence=0.5,  # Below 0.6 threshold
                language="ru",
                duration_ms=2000,
            )
        )

        with pytest.raises(RuntimeError, match="Не удалось распознать голос"):
            await use_case.execute(input_data)

        # Verify command not stored
        use_case.command_store.save.assert_not_called()

        # Verify confirmation not sent
        use_case.confirmation_gateway.send_confirmation.assert_not_called()

    async def test_execute_duration_exceeds_limit(
        self,
        use_case: ProcessVoiceCommandUseCase,
    ) -> None:
        """Handle audio duration exceeding limit (validated in DTO)."""
        # Note: Duration validation happens in ProcessVoiceCommandInput.__post_init__
        # This test verifies that use case would reject it if DTO validation is bypassed
        # For normal flow, DTO validation prevents this case
        command_id = uuid4()

        # Create DTO with valid duration (otherwise DTO creation fails)
        input_data = ProcessVoiceCommandInput(
            command_id=command_id,
            user_id="123456789",
            audio_bytes=b"audio data",
            duration_seconds=120.0,  # Exactly at limit
        )

        # Manually modify duration to test use case validation (bypassing DTO)
        input_data.duration_seconds = 121.0

        with pytest.raises(ValueError, match="exceeds maximum 120 seconds"):
            await use_case.execute(input_data)

    async def test_execute_storage_error(
        self,
        use_case: ProcessVoiceCommandUseCase,
        mock_command_store: AsyncMock,
    ) -> None:
        """Handle storage error."""
        command_id = uuid4()
        input_data = ProcessVoiceCommandInput(
            command_id=command_id,
            user_id="123456789",
            audio_bytes=b"audio data",
            duration_seconds=3.5,
        )

        mock_command_store.save = AsyncMock(side_effect=Exception("Storage error"))

        with pytest.raises(RuntimeError, match="Failed to store voice command"):
            await use_case.execute(input_data)

        # Verify confirmation not sent
        use_case.confirmation_gateway.send_confirmation.assert_not_called()
