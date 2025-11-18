"""Process voice command use case.

Purpose:
    Handles voice command processing: transcription via STT adapter,
    saving to store, and optionally sending confirmation.
"""

from uuid import UUID

from src.application.voice.dtos import (
    ProcessVoiceCommandInput,
    TranscriptionOutput,
)
from src.domain.interfaces.voice import (
    SpeechToTextAdapter,
    VoiceCommandStore,
)
from src.infrastructure.logging import get_logger

logger = get_logger("voice.process_voice_command")


class ProcessVoiceCommandUseCase:
    """Use case for processing voice commands.

    Purpose:
        Transcribes audio via STT adapter, saves to store,
        and returns transcription result. Note: confirmation
        is disabled - commands are executed immediately after
        transcription in voice_handler.py.

    Args:
        stt_adapter: Speech-to-text adapter for transcription.
        command_store: Voice command store for saving transcripts.
    """

    def __init__(
        self,
        stt_adapter: SpeechToTextAdapter,
        command_store: VoiceCommandStore,
    ) -> None:
        self.stt_adapter = stt_adapter
        self.command_store = command_store

    async def execute(
        self,
        input_data: ProcessVoiceCommandInput,
    ) -> TranscriptionOutput:
        """Process voice command.

        Purpose:
            Transcribes audio, saves to store, and returns result.

        Args:
            input_data: Input DTO with command ID, user ID, audio bytes, duration.

        Returns:
            TranscriptionOutput with text, confidence, language, duration.

        Raises:
            RuntimeError: If transcription or storage fails.

        Example:
            >>> use_case = ProcessVoiceCommandUseCase(stt_adapter, command_store)
            >>> input_data = ProcessVoiceCommandInput(...)
            >>> result = await use_case.execute(input_data)
            >>> result.text
            'Привет, мир!'
        """
        logger.info(
            "Processing voice command",
            extra={
                "command_id": str(input_data.command_id),
                "user_id": input_data.user_id,
                "duration_seconds": input_data.duration_seconds,
            },
        )

        # Transcribe audio via STT adapter
        transcription = await self.stt_adapter.transcribe(
            audio_bytes=input_data.audio_bytes,
            language="ru",  # Default to Russian
        )

        # Save transcribed text to store
        try:
            await self.command_store.save(
                command_id=str(input_data.command_id),
                user_id=input_data.user_id,
                text=transcription.text,
                ttl_seconds=300,  # 5 minutes TTL
            )

            logger.info(
                "Voice command saved to store",
                extra={
                    "command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to save voice command",
                extra={
                    "command_id": str(input_data.command_id),
                    "user_id": input_data.user_id,
                    "error": str(e),
                },
            )
            raise RuntimeError("Failed to store voice command") from e

        # Note: Confirmation is disabled - commands are executed immediately
        # after transcription in voice_handler.py
        # No need to send confirmation message with buttons

        return TranscriptionOutput(
            text=transcription.text,
            confidence=transcription.confidence,
            language=transcription.language,
            duration_ms=transcription.duration_ms,
        )

