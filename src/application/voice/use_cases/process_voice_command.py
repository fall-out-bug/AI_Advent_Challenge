"""Process voice command use case.

Purpose:
    Handles voice command processing: validates audio, transcribes via STT,
    checks confidence threshold, stores command, and triggers confirmation.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from src.application.voice.dtos import ProcessVoiceCommandInput
from src.domain.interfaces import ConfirmationGateway
from src.domain.voice.exceptions import SpeechToTextError
from src.domain.voice.interfaces import SpeechToTextService
from src.domain.voice.value_objects import (
    TranscriptionResult,
    VoiceCommand,
    VoiceCommandState,
)
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.voice.command_store import VoiceCommandStore

logger = get_logger("use_cases.process_voice_command")


class ProcessVoiceCommandUseCase:
    """Use case for processing voice commands.

    Purpose:
        Validates audio metadata, transcribes via STT service, checks
        confidence threshold, stores command if confidence ≥ threshold,
        and triggers confirmation message to user.

    Args:
        stt_service: Speech-to-text service (Ollama or Vosk adapter).
        command_store: Voice command storage (Redis or in-memory).
        confirmation_gateway: Gateway for sending confirmation messages.
        settings: Optional settings instance (defaults to get_settings()).
    """

    def __init__(
        self,
        stt_service: SpeechToTextService,
        command_store: VoiceCommandStore,
        confirmation_gateway: ConfirmationGateway,
        settings: Optional[Settings] = None,
    ) -> None:
        self.stt_service = stt_service
        self.command_store = command_store
        self.confirmation_gateway = confirmation_gateway
        self.settings = settings or get_settings()

    async def execute(
        self,
        input_data: ProcessVoiceCommandInput,
    ) -> TranscriptionResult:
        """Execute voice command processing.

        Purpose:
            Processes voice command: validates duration, transcribes audio,
            checks confidence, stores command if valid, sends confirmation.

        Args:
            input_data: Voice command input with audio bytes and metadata.

        Returns:
            TranscriptionResult with text, confidence, language, duration_ms.

        Raises:
            ValueError: If audio duration exceeds 120 seconds (already validated in DTO).
            SpeechToTextError: If STT transcription fails.
            RuntimeError: If confidence below threshold or storage fails.

        Example:
            >>> use_case = ProcessVoiceCommandUseCase(...)
            >>> input_data = ProcessVoiceCommandInput(
            ...     command_id=uuid4(),
            ...     user_id="123456789",
            ...     audio_bytes=b"...",
            ...     duration_seconds=3.5
            ... )
            >>> result = await use_case.execute(input_data)
            >>> result.text
            "Сделай дайджест по каналу X"
        """
        logger.info(
            "Processing voice command",
            extra={
                "voice_command_id": str(input_data.command_id),
                "user_id": input_data.user_id,
                "duration_seconds": input_data.duration_seconds,
            },
        )

        # Note: Duration validation is already done in ProcessVoiceCommandInput.__post_init__
        # But we check again for safety
        if input_data.duration_seconds > 120:
            error_msg = (
                f"Audio duration {input_data.duration_seconds}s exceeds "
                "maximum 120 seconds"
            )
            logger.error(
                error_msg,
                extra={
                    "voice_command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                    "duration_seconds": input_data.duration_seconds,
                },
            )
            raise ValueError(error_msg)

        # Transcribe audio via STT service
        try:
            transcription = await self.stt_service.transcribe(
                audio=input_data.audio_bytes,
                language="ru",
            )

            logger.info(
                "Voice transcription completed",
                extra={
                    "voice_command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                    "transcription_length": len(transcription.text),
                    "confidence_score": transcription.confidence,
                    "language": transcription.language,
                },
            )

        except SpeechToTextError as e:
            logger.error(
                "STT transcription failed",
                extra={
                    "voice_command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                    "error": str(e),
                },
            )
            # Send error message to user via confirmation gateway
            # (we'll use it for error messages too, even though it's called "confirmation")
            # Actually, on STT failure we shouldn't send confirmation, just error message
            # But for MVP we can reuse the gateway for simplicity
            raise

        # Check confidence threshold
        min_confidence = self.settings.stt_min_confidence
        if transcription.confidence < min_confidence:
            error_msg = (
                f"STT confidence {transcription.confidence:.2f} below "
                f"threshold {min_confidence:.2f}"
            )
            logger.warning(
                error_msg,
                extra={
                    "voice_command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                    "confidence_score": transcription.confidence,
                    "min_confidence": min_confidence,
                },
            )
            raise RuntimeError(
                "Не удалось распознать голос. Попробуйте записать заново."
            )

        # Store voice command with TTL
        command = VoiceCommand(
            id=input_data.command_id,
            user_id=input_data.user_id,
            transcription=transcription,
            state=VoiceCommandState.PENDING,
        )

        try:
            ttl_seconds = self.settings.voice_command_ttl_seconds
            await self.command_store.save(command, ttl_seconds=ttl_seconds)

            logger.info(
                "Voice command stored",
                extra={
                    "voice_command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                    "ttl_seconds": ttl_seconds,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to store voice command",
                extra={
                    "voice_command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                    "error": str(e),
                },
            )
            raise RuntimeError("Failed to store voice command") from e

        # Note: Confirmation is disabled - commands are executed immediately
        # after transcription in voice_handler.py
        # No need to send confirmation message with buttons

        return transcription


