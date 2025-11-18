"""Voice command data transfer objects.

Purpose:
    Defines DTOs for voice command use cases.
"""

from dataclasses import dataclass
from uuid import UUID


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

    Example:
        >>> input_data = ProcessVoiceCommandInput(
        ...     command_id=UUID("12345678-1234-5678-1234-567812345678"),
        ...     user_id="123456789",
        ...     audio_bytes=b"...",
        ...     duration_seconds=2.5,
        ... )
    """

    command_id: UUID
    user_id: str
    audio_bytes: bytes
    duration_seconds: float


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

    Example:
        >>> input_data = HandleVoiceConfirmationInput(
        ...     command_id=UUID("12345678-1234-5678-1234-567812345678"),
        ...     user_id="123456789",
        ...     action="confirm",
        ... )
    """

    command_id: UUID
    user_id: str
    action: str  # "confirm" or "reject"


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

