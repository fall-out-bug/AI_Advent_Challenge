"""Voice command domain protocols.

Purpose:
    Defines domain interfaces for voice command processing:
    - SpeechToTextAdapter: STT transcription protocol
    - VoiceCommandStore: Command storage protocol
    - ConfirmationGateway: Confirmation messaging protocol (deprecated)
    - ButlerGateway: Butler routing protocol
"""

from abc import ABC, abstractmethod
from typing import Protocol

from src.domain.value_objects.transcription import Transcription


class SpeechToTextAdapter(Protocol):
    """Protocol for speech-to-text transcription.

    Purpose:
        Defines interface for transcribing audio data to text.
        Implementations may use Whisper, Google Speech, or other STT services.
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "ru",
        model: str | None = None,
    ) -> Transcription:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data bytes.
            language: Language code (default: "ru" for Russian).
            model: Optional model override.

        Returns:
            Transcription value object with text, confidence, and metadata.

        Raises:
            RuntimeError: If transcription fails.
        """
        ...


class VoiceCommandStore(Protocol):
    """Protocol for storing transcribed voice commands.

    Purpose:
        Defines interface for temporarily storing transcribed commands
        before execution. Used for confirmation flow (deprecated).
    """

    @abstractmethod
    async def save(
        self,
        command_id: str,
        user_id: str,
        text: str,
        ttl_seconds: int = 300,
    ) -> None:
        """Save transcribed command text.

        Args:
            command_id: Unique command identifier.
            user_id: User identifier (Telegram user ID).
            text: Transcribed command text.
            ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes).

        Raises:
            RuntimeError: If save fails.
        """
        ...

    @abstractmethod
    async def get(
        self,
        command_id: str,
        user_id: str,
    ) -> str | None:
        """Get stored command text.

        Args:
            command_id: Unique command identifier.
            user_id: User identifier (Telegram user ID).

        Returns:
            Stored command text, or None if not found or expired.
        """
        ...

    @abstractmethod
    async def delete(
        self,
        command_id: str,
        user_id: str,
    ) -> None:
        """Delete stored command.

        Args:
            command_id: Unique command identifier.
            user_id: User identifier (Telegram user ID).
        """
        ...


class ConfirmationGateway(Protocol):
    """Protocol for sending confirmation messages (deprecated).

    Purpose:
        Defines interface for sending confirmation messages with buttons.
        Deprecated in favor of immediate execution.
    """

    @abstractmethod
    async def send_confirmation(
        self,
        user_id: str,
        text: str,
        command_id: str,
    ) -> None:
        """Send confirmation message with buttons.

        Args:
            user_id: User identifier (Telegram user ID).
            text: Transcribed command text to confirm.
            command_id: Unique command identifier.

        Raises:
            RuntimeError: If sending fails.
        """
        ...


class ButlerGateway(Protocol):
    """Protocol for routing voice commands to Butler.

    Purpose:
        Defines interface for routing confirmed voice commands
        to Butler orchestrator for execution.
    """

    @abstractmethod
    async def handle_user_message(
        self,
        user_id: str,
        text: str,
        session_id: str,
    ) -> str:
        """Route voice command text to Butler pipeline.

        Args:
            user_id: User identifier (Telegram user ID).
            text: Transcribed command text.
            session_id: Session identifier (generated as f"voice_{user_id}_{command_id}").

        Returns:
            Response text from Butler orchestrator.

        Raises:
            RuntimeError: If routing fails.
        """
        ...
