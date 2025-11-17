"""Domain exceptions for voice agent.

Purpose:
    Defines domain-specific errors for voice-to-text processing
    and command validation.
"""

from src.domain.exceptions.domain_errors import DomainError


class SpeechToTextError(DomainError):
    """Raised when speech-to-text transcription fails.

    Purpose:
        Indicates that STT processing failed due to audio decoding
        errors, model unavailability, or unsupported audio format.

    Args:
        message: Error message describing the failure.
        audio_format: Optional audio format that caused the error.
    """

    def __init__(
        self,
        message: str,
        audio_format: str | None = None,
    ) -> None:
        """Initialize speech-to-text error.

        Args:
            message: Error message.
            audio_format: Optional audio format that caused the error.
        """
        super().__init__(message, error_code="SPEECH_TO_TEXT_ERROR")
        self.audio_format = audio_format


class InvalidVoiceCommandError(DomainError):
    """Raised when voice command validation fails.

    Purpose:
        Indicates that a voice command is invalid (e.g., wrong state,
        expired, missing transcription).

    Args:
        message: Error message describing the validation failure.
        command_id: Optional command identifier that caused the error.
    """

    def __init__(
        self,
        message: str,
        command_id: str | None = None,
    ) -> None:
        """Initialize invalid voice command error.

        Args:
            message: Error message.
            command_id: Optional command identifier.
        """
        super().__init__(message, error_code="INVALID_VOICE_COMMAND")
        self.command_id = command_id


