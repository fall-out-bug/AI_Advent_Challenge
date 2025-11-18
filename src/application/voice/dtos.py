<<<<<<< HEAD
"""Voice command data transfer objects.

Purpose:
    Defines DTOs for voice command use cases.
"""

=======
"""DTOs for voice agent use cases.

Purpose:
    Defines input/output data transfer objects for voice command
    processing and confirmation use cases.
"""

from __future__ import annotations

>>>>>>> origin/master
from dataclasses import dataclass
from uuid import UUID


<<<<<<< HEAD
@dataclass(frozen=True)
class ProcessVoiceCommandInput:
    """Input DTO for ProcessVoiceCommandUseCase.

    Purpose:
        Contains input data for processing a voice command:
        command ID, user ID, audio bytes, and duration.

    Attributes:
        command_id: Unique command identifier (UUID).
        user_id: User identifier (Telegram user ID).
        audio_bytes: Raw audio data bytes.
        duration_seconds: Audio duration in seconds.

=======
@dataclass
class ProcessVoiceCommandInput:
    """Input for processing voice command use case.

    Purpose:
        Encapsulates all necessary parameters for processing a voice command,
        including audio data, user information, and metadata.

    Args:
        command_id: Unique command identifier (UUID).
        user_id: Telegram user identifier.
        audio_bytes: Raw audio bytes from Telegram (OGG/OPUS format).
        duration_seconds: Audio duration in seconds.

    Constraints:
        - Duration must be <= 120 seconds (enforced in use case).
        - Audio bytes must be non-empty (enforced in use case).

>>>>>>> origin/master
    Example:
        >>> input_data = ProcessVoiceCommandInput(
        ...     command_id=UUID("12345678-1234-5678-1234-567812345678"),
        ...     user_id="123456789",
        ...     audio_bytes=b"...",
<<<<<<< HEAD
        ...     duration_seconds=2.5,
        ... )
=======
        ...     duration_seconds=3.5
        ... )
        >>> input_data.duration_seconds
        3.5
>>>>>>> origin/master
    """

    command_id: UUID
    user_id: str
    audio_bytes: bytes
    duration_seconds: float

<<<<<<< HEAD

@dataclass(frozen=True)
class HandleVoiceConfirmationInput:
    """Input DTO for HandleVoiceConfirmationUseCase.

    Purpose:
        Contains input data for handling voice command confirmation:
        command ID, user ID, and action (confirm/reject).

    Attributes:
        command_id: Unique command identifier (UUID).
        user_id: User identifier (Telegram user ID).
        action: Action type: "confirm" or "reject".
=======
    def __post_init__(self) -> None:
        """Validate input data."""
        if not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        if not self.audio_bytes:
            raise ValueError("Audio bytes cannot be empty")
        if self.duration_seconds < 0:
            raise ValueError(
                f"Duration must be non-negative, got {self.duration_seconds}"
            )
        if self.duration_seconds > 120:
            raise ValueError(
                f"Duration must be <= 120 seconds, got {self.duration_seconds}"
            )


@dataclass
class HandleVoiceConfirmationInput:
    """Input for handling voice command confirmation use case.

    Purpose:
        Encapsulates parameters for processing user confirmation or rejection
        of a transcribed voice command.

    Args:
        command_id: Unique command identifier (UUID) to confirm or reject.
        user_id: Telegram user identifier (for validation).
        action: Confirmation action ("confirm" or "reject").
>>>>>>> origin/master

    Example:
        >>> input_data = HandleVoiceConfirmationInput(
        ...     command_id=UUID("12345678-1234-5678-1234-567812345678"),
        ...     user_id="123456789",
<<<<<<< HEAD
        ...     action="confirm",
        ... )
=======
        ...     action="confirm"
        ... )
        >>> input_data.action
        'confirm'
>>>>>>> origin/master
    """

    command_id: UUID
    user_id: str
    action: str  # "confirm" or "reject"

<<<<<<< HEAD

@dataclass(frozen=True)
class TranscriptionOutput:
    """Output DTO for voice transcription.

    Purpose:
        Contains transcription result with text, confidence, and metadata.

    Attributes:
        text: Transcribed text content.
        confidence: Confidence score (0.0 to 1.0).
        language: Detected language code.
        duration_ms: Audio duration in milliseconds.

    Example:
        >>> output = TranscriptionOutput(
        ...     text="Привет, мир!",
        ...     confidence=0.95,
        ...     language="ru",
        ...     duration_ms=2000,
        ... )
    """

    text: str
    confidence: float
    language: str
    duration_ms: int
=======
    def __post_init__(self) -> None:
        """Validate input data."""
        if not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        if self.action not in ("confirm", "reject"):
            raise ValueError(
                f"Action must be 'confirm' or 'reject', got '{self.action}'"
            )

>>>>>>> origin/master
