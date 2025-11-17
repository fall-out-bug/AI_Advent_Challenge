"""Unit tests for voice application DTOs.

Purpose:
    Tests validation and edge cases for ProcessVoiceCommandInput
    and HandleVoiceConfirmationInput DTOs.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.application.voice.dtos import (
    HandleVoiceConfirmationInput,
    ProcessVoiceCommandInput,
)


class TestProcessVoiceCommandInput:
    """Test ProcessVoiceCommandInput DTO."""

    def test_process_voice_command_input_valid(self) -> None:
        """Valid input is created successfully."""
        command_id = uuid4()
        input_data = ProcessVoiceCommandInput(
            command_id=command_id,
            user_id="123456789",
            audio_bytes=b"audio data",
            duration_seconds=3.5,
        )

        assert input_data.command_id == command_id
        assert input_data.user_id == "123456789"
        assert input_data.audio_bytes == b"audio data"
        assert input_data.duration_seconds == 3.5

    def test_process_voice_command_input_empty_user_id_raises_error(self) -> None:
        """Input with empty user ID raises ValueError."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            ProcessVoiceCommandInput(
                command_id=uuid4(),
                user_id="",
                audio_bytes=b"audio",
                duration_seconds=3.0,
            )

        with pytest.raises(ValueError, match="User ID cannot be empty"):
            ProcessVoiceCommandInput(
                command_id=uuid4(),
                user_id="   ",
                audio_bytes=b"audio",
                duration_seconds=3.0,
            )

    def test_process_voice_command_input_empty_audio_raises_error(self) -> None:
        """Input with empty audio bytes raises ValueError."""
        with pytest.raises(ValueError, match="Audio bytes cannot be empty"):
            ProcessVoiceCommandInput(
                command_id=uuid4(),
                user_id="123456789",
                audio_bytes=b"",
                duration_seconds=3.0,
            )

    def test_process_voice_command_input_negative_duration_raises_error(
        self,
    ) -> None:
        """Input with negative duration raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be non-negative"):
            ProcessVoiceCommandInput(
                command_id=uuid4(),
                user_id="123456789",
                audio_bytes=b"audio",
                duration_seconds=-1.0,
            )

    def test_process_voice_command_input_duration_too_long_raises_error(
        self,
    ) -> None:
        """Input with duration > 120 seconds raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be <= 120 seconds"):
            ProcessVoiceCommandInput(
                command_id=uuid4(),
                user_id="123456789",
                audio_bytes=b"audio",
                duration_seconds=121.0,
            )

        # Boundary: exactly 120 seconds should be valid
        ProcessVoiceCommandInput(
            command_id=uuid4(),
            user_id="123456789",
            audio_bytes=b"audio",
            duration_seconds=120.0,
        )

    def test_process_voice_command_input_zero_duration_valid(self) -> None:
        """Input with zero duration is valid (edge case)."""
        input_data = ProcessVoiceCommandInput(
            command_id=uuid4(),
            user_id="123456789",
            audio_bytes=b"audio",
            duration_seconds=0.0,
        )

        assert input_data.duration_seconds == 0.0


class TestHandleVoiceConfirmationInput:
    """Test HandleVoiceConfirmationInput DTO."""

    def test_handle_voice_confirmation_input_valid_confirm(self) -> None:
        """Valid confirm input is created successfully."""
        command_id = uuid4()
        input_data = HandleVoiceConfirmationInput(
            command_id=command_id,
            user_id="123456789",
            action="confirm",
        )

        assert input_data.command_id == command_id
        assert input_data.user_id == "123456789"
        assert input_data.action == "confirm"

    def test_handle_voice_confirmation_input_valid_reject(self) -> None:
        """Valid reject input is created successfully."""
        command_id = uuid4()
        input_data = HandleVoiceConfirmationInput(
            command_id=command_id,
            user_id="123456789",
            action="reject",
        )

        assert input_data.action == "reject"

    def test_handle_voice_confirmation_input_empty_user_id_raises_error(
        self,
    ) -> None:
        """Input with empty user ID raises ValueError."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            HandleVoiceConfirmationInput(
                command_id=uuid4(),
                user_id="",
                action="confirm",
            )

        with pytest.raises(ValueError, match="User ID cannot be empty"):
            HandleVoiceConfirmationInput(
                command_id=uuid4(),
                user_id="   ",
                action="confirm",
            )

    def test_handle_voice_confirmation_input_invalid_action_raises_error(
        self,
    ) -> None:
        """Input with invalid action raises ValueError."""
        with pytest.raises(
            ValueError,
            match="Action must be 'confirm' or 'reject'",
        ):
            HandleVoiceConfirmationInput(
                command_id=uuid4(),
                user_id="123456789",
                action="invalid",
            )

        with pytest.raises(
            ValueError,
            match="Action must be 'confirm' or 'reject'",
        ):
            HandleVoiceConfirmationInput(
                command_id=uuid4(),
                user_id="123456789",
                action="",
            )


