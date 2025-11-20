"""Value objects for voice agent domain.

Purpose:
    Defines immutable value objects for transcription results,
    voice commands, and command states.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import UUID

from src.domain.voice.exceptions import InvalidVoiceCommandError


class VoiceCommandState(str, Enum):
    """Voice command state.

    Purpose:
        Represents the lifecycle state of a voice command.

    Values:
        PENDING: Command transcribed, awaiting user confirmation.
        CONFIRMED: Command confirmed by user, sent to Butler.
        REJECTED: Command rejected by user, should be re-recorded.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class TranscriptionResult:
    """Result of speech-to-text transcription.

    Purpose:
        Encapsulates the result of STT processing, including
        transcribed text, confidence score, language, and duration.

    Args:
        text: Transcribed text from audio.
        confidence: Confidence score (0.0 to 1.0).
        language: ISO language code (e.g., "ru", "en").
        duration_ms: Audio duration in milliseconds.

    Example:
        >>> result = TranscriptionResult(
        ...     text="Сделай дайджест по каналу X",
        ...     confidence=0.85,
        ...     language="ru",
        ...     duration_ms=3000
        ... )
        >>> result.confidence
        0.85
    """

    text: str
    confidence: float
    language: str = "ru"
    duration_ms: int = 0

    def __post_init__(self) -> None:
        """Validate transcription result."""
        if not self.text.strip():
            raise ValueError("Transcription text cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
        if self.duration_ms < 0:
            raise ValueError(f"Duration must be non-negative, got {self.duration_ms}")


@dataclass
class VoiceCommand:
    """Voice command entity.

    Purpose:
        Represents a voice command with its transcription,
        user information, and confirmation state.

    Args:
        id: Unique command identifier (UUID).
        user_id: Telegram user identifier.
        transcription: Transcription result from STT.
        state: Current command state (PENDING, CONFIRMED, REJECTED).
        created_at: Timestamp when command was created (Unix seconds).
        expires_at: Timestamp when command expires (Unix seconds, None if no expiry).

    Example:
        >>> command = VoiceCommand(
        ...     id=UUID("12345678-1234-5678-1234-567812345678"),
        ...     user_id="123456789",
        ...     transcription=TranscriptionResult(
        ...         text="Сделай дайджест",
        ...         confidence=0.85,
        ...         language="ru",
        ...         duration_ms=2000
        ...     ),
        ...     state=VoiceCommandState.PENDING
        ... )
        >>> command.state
        <VoiceCommandState.PENDING: 'pending'>
    """

    id: UUID
    user_id: str
    transcription: TranscriptionResult
    state: VoiceCommandState = VoiceCommandState.PENDING
    created_at: Optional[float] = None
    expires_at: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate voice command."""
        if not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        if self.created_at is not None and self.created_at < 0:
            raise ValueError(
                f"Created timestamp must be non-negative, got {self.created_at}"
            )
        if (
            self.expires_at is not None
            and self.created_at is not None
            and self.expires_at <= self.created_at
        ):
            raise ValueError(
                f"Expires timestamp must be after created timestamp: "
                f"{self.expires_at} <= {self.created_at}"
            )

    def confirm(self) -> None:
        """Mark command as confirmed.

        Raises:
            InvalidVoiceCommandError: If command is not in PENDING state.
        """
        if self.state != VoiceCommandState.PENDING:
            raise InvalidVoiceCommandError(
                f"Cannot confirm command in state {self.state}, "
                "only PENDING commands can be confirmed"
            )
        self.state = VoiceCommandState.CONFIRMED

    def reject(self) -> None:
        """Mark command as rejected.

        Raises:
            InvalidVoiceCommandError: If command is not in PENDING state.
        """
        if self.state != VoiceCommandState.PENDING:
            raise InvalidVoiceCommandError(
                f"Cannot reject command in state {self.state}, "
                "only PENDING commands can be rejected"
            )
        self.state = VoiceCommandState.REJECTED

    def is_expired(self, current_time: float) -> bool:
        """Check if command has expired.

        Args:
            current_time: Current Unix timestamp in seconds.

        Returns:
            True if command has expired, False otherwise.
        """
        if self.expires_at is None:
            return False
        return current_time >= self.expires_at
