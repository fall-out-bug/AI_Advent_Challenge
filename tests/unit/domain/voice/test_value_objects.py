"""Unit tests for voice domain value objects.

Purpose:
    Tests validation, state transitions, and edge cases for
    TranscriptionResult, VoiceCommand, and related value objects.
"""

from __future__ import annotations

import time
from uuid import UUID, uuid4

import pytest

from src.domain.voice.exceptions import InvalidVoiceCommandError
from src.domain.voice.value_objects import (
    TranscriptionResult,
    VoiceCommand,
    VoiceCommandState,
)


class TestTranscriptionResult:
    """Test TranscriptionResult value object."""

    def test_transcription_result_valid(self) -> None:
        """Valid transcription result is created successfully."""
        result = TranscriptionResult(
            text="Сделай дайджест по каналу X",
            confidence=0.85,
            language="ru",
            duration_ms=3000,
        )

        assert result.text == "Сделай дайджест по каналу X"
        assert result.confidence == 0.85
        assert result.language == "ru"
        assert result.duration_ms == 3000

    def test_transcription_result_defaults(self) -> None:
        """Transcription result uses default values for optional fields."""
        result = TranscriptionResult(text="Test", confidence=0.9)

        assert result.text == "Test"
        assert result.confidence == 0.9
        assert result.language == "ru"
        assert result.duration_ms == 0

    def test_transcription_result_empty_text_raises_error(self) -> None:
        """Transcription result with empty text raises ValueError."""
        with pytest.raises(ValueError, match="Transcription text cannot be empty"):
            TranscriptionResult(text="", confidence=0.85)

        with pytest.raises(ValueError, match="Transcription text cannot be empty"):
            TranscriptionResult(text="   ", confidence=0.85)

    def test_transcription_result_confidence_bounds(self) -> None:
        """Transcription result validates confidence bounds."""
        # Valid boundaries
        TranscriptionResult(text="Test", confidence=0.0)
        TranscriptionResult(text="Test", confidence=1.0)
        TranscriptionResult(text="Test", confidence=0.5)

        # Invalid: negative
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            TranscriptionResult(text="Test", confidence=-0.1)

        # Invalid: > 1.0
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            TranscriptionResult(text="Test", confidence=1.1)

    def test_transcription_result_negative_duration_raises_error(self) -> None:
        """Transcription result with negative duration raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be non-negative"):
            TranscriptionResult(text="Test", confidence=0.85, duration_ms=-100)


class TestVoiceCommandState:
    """Test VoiceCommandState enum."""

    def test_voice_command_state_values(self) -> None:
        """Voice command state has correct values."""
        assert VoiceCommandState.PENDING == "pending"
        assert VoiceCommandState.CONFIRMED == "confirmed"
        assert VoiceCommandState.REJECTED == "rejected"


class TestVoiceCommand:
    """Test VoiceCommand value object."""

    def test_voice_command_valid(self) -> None:
        """Valid voice command is created successfully."""
        command_id = uuid4()
        transcription = TranscriptionResult(
            text="Сделай дайджест",
            confidence=0.85,
            language="ru",
            duration_ms=2000,
        )

        command = VoiceCommand(
            id=command_id,
            user_id="123456789",
            transcription=transcription,
            state=VoiceCommandState.PENDING,
        )

        assert command.id == command_id
        assert command.user_id == "123456789"
        assert command.transcription == transcription
        assert command.state == VoiceCommandState.PENDING
        assert command.created_at is None
        assert command.expires_at is None

    def test_voice_command_default_state(self) -> None:
        """Voice command defaults to PENDING state."""
        command = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
        )

        assert command.state == VoiceCommandState.PENDING

    def test_voice_command_empty_user_id_raises_error(self) -> None:
        """Voice command with empty user ID raises ValueError."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            VoiceCommand(
                id=uuid4(),
                user_id="",
                transcription=TranscriptionResult(text="Test", confidence=0.9),
            )

        with pytest.raises(ValueError, match="User ID cannot be empty"):
            VoiceCommand(
                id=uuid4(),
                user_id="   ",
                transcription=TranscriptionResult(text="Test", confidence=0.9),
            )

    def test_voice_command_negative_created_at_raises_error(self) -> None:
        """Voice command with negative created_at raises ValueError."""
        with pytest.raises(ValueError, match="Created timestamp must be non-negative"):
            VoiceCommand(
                id=uuid4(),
                user_id="123456789",
                transcription=TranscriptionResult(text="Test", confidence=0.9),
                created_at=-1.0,
            )

    def test_voice_command_expires_at_before_created_at_raises_error(self) -> None:
        """Voice command with expires_at <= created_at raises ValueError."""
        now = time.time()

        with pytest.raises(
            ValueError,
            match="Expires timestamp must be after created timestamp",
        ):
            VoiceCommand(
                id=uuid4(),
                user_id="123456789",
                transcription=TranscriptionResult(text="Test", confidence=0.9),
                created_at=now,
                expires_at=now - 1.0,
            )

        with pytest.raises(
            ValueError,
            match="Expires timestamp must be after created timestamp",
        ):
            VoiceCommand(
                id=uuid4(),
                user_id="123456789",
                transcription=TranscriptionResult(text="Test", confidence=0.9),
                created_at=now,
                expires_at=now,
            )

    def test_voice_command_confirm_success(self) -> None:
        """Confirming PENDING command changes state to CONFIRMED."""
        command = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
            state=VoiceCommandState.PENDING,
        )

        command.confirm()

        assert command.state == VoiceCommandState.CONFIRMED

    def test_voice_command_confirm_non_pending_raises_error(self) -> None:
        """Confirming non-PENDING command raises InvalidVoiceCommandError."""
        command_confirmed = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
            state=VoiceCommandState.CONFIRMED,
        )

        with pytest.raises(InvalidVoiceCommandError):
            command_confirmed.confirm()

        command_rejected = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
            state=VoiceCommandState.REJECTED,
        )

        with pytest.raises(InvalidVoiceCommandError):
            command_rejected.confirm()

    def test_voice_command_reject_success(self) -> None:
        """Rejecting PENDING command changes state to REJECTED."""
        command = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
            state=VoiceCommandState.PENDING,
        )

        command.reject()

        assert command.state == VoiceCommandState.REJECTED

    def test_voice_command_reject_non_pending_raises_error(self) -> None:
        """Rejecting non-PENDING command raises InvalidVoiceCommandError."""
        command_confirmed = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
            state=VoiceCommandState.CONFIRMED,
        )

        with pytest.raises(InvalidVoiceCommandError):
            command_confirmed.reject()

        command_rejected = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
            state=VoiceCommandState.REJECTED,
        )

        with pytest.raises(InvalidVoiceCommandError):
            command_rejected.reject()

    def test_voice_command_is_expired_no_expiry(self) -> None:
        """Command without expiry never returns True for is_expired."""
        command = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
        )

        assert not command.is_expired(time.time())

    def test_voice_command_is_expired_not_expired(self) -> None:
        """Command is not expired before expires_at timestamp."""
        now = time.time()
        command = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
            created_at=now,
            expires_at=now + 600.0,  # 10 minutes
        )

        assert not command.is_expired(now + 300.0)  # 5 minutes later

    def test_voice_command_is_expired_expired(self) -> None:
        """Command is expired after expires_at timestamp."""
        now = time.time()
        command = VoiceCommand(
            id=uuid4(),
            user_id="123456789",
            transcription=TranscriptionResult(text="Test", confidence=0.9),
            created_at=now,
            expires_at=now + 600.0,  # 10 minutes
        )

        assert command.is_expired(now + 600.0)  # Exactly at expiry
        assert command.is_expired(now + 700.0)  # After expiry
