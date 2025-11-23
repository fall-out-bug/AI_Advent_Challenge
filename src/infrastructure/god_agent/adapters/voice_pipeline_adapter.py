"""Voice Pipeline Adapter for God Agent."""

import base64
from typing import Optional

from aiogram import Bot
from aiogram.types import Message

from src.application.voice.dtos import ProcessVoiceCommandInput
from src.application.voice.use_cases.process_voice_command import (
    ProcessVoiceCommandUseCase,
)
from src.infrastructure.logging import get_logger

logger = get_logger("voice_pipeline_adapter")


class VoicePipelineAdapter:
    """Voice Pipeline Adapter.

    Purpose:
        Wraps ProcessVoiceCommandUseCase to provide voice transcription
        interface for God Agent.

    Attributes:
        process_voice_command_use_case: Use case for voice command processing.
        bot: Optional Telegram bot instance for downloading voice files.

    Example:
        >>> adapter = VoicePipelineAdapter(process_voice_command_use_case)
        >>> text = await adapter.transcribe_voice(message)
        >>> text
        'Hello, how can you help me?'
    """

    def __init__(
        self,
        process_voice_command_use_case: ProcessVoiceCommandUseCase,
        bot: Optional[Bot] = None,
    ) -> None:
        """Initialize voice pipeline adapter.

        Args:
            process_voice_command_use_case: Use case for voice command processing.
            bot: Optional Telegram bot instance for downloading voice files.
        """
        self.process_voice_command_use_case = process_voice_command_use_case
        self.bot = bot
        logger.info("VoicePipelineAdapter initialized")

    async def transcribe_voice(self, message: Message) -> str:
        """Transcribe voice message to text.

        Purpose:
            Downloads voice file, processes through ProcessVoiceCommandUseCase,
            and returns transcribed text.

        Args:
            message: Telegram message with voice/audio.

        Returns:
            Transcribed text or empty string if transcription fails.

        Example:
            >>> text = await adapter.transcribe_voice(message)
            >>> text
            'Hello, how can you help me?'
        """
        try:
            if not message.from_user:
                logger.warning("Voice message has no user")
                return ""

            user_id = str(message.from_user.id)

            # Get voice file
            voice = message.voice or message.audio
            if not voice:
                logger.warning("Message has no voice or audio")
                return ""

            # Download voice file
            audio_bytes = await self._download_voice_file(voice.file_id)

            if not audio_bytes:
                logger.warning("Failed to download voice file")
                return ""

            # Create input
            from uuid import uuid4

            input_data = ProcessVoiceCommandInput(
                command_id=uuid4(),
                user_id=user_id,
                audio_bytes=audio_bytes,
                duration_seconds=voice.duration or 0,
            )

            # Execute use case
            result = await self.process_voice_command_use_case.execute(input_data)

            return result.text

        except Exception as e:
            logger.error(
                "Voice transcription failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            return ""

    def is_voice_message(self, message: Message) -> bool:
        """Check if message is a voice message.

        Purpose:
            Determines if message contains voice or audio content.

        Args:
            message: Telegram message object.

        Returns:
            True if message is voice/audio, False otherwise.

        Example:
            >>> is_voice = adapter.is_voice_message(message)
            >>> is_voice
            True
        """
        return message.voice is not None or message.audio is not None

    async def _download_voice_file(self, file_id: str) -> Optional[bytes]:
        """Download voice file from Telegram.

        Args:
            file_id: Telegram file identifier.

        Returns:
            Audio bytes or None if download fails.
        """
        if not self.bot:
            logger.warning("Bot instance not available for voice download")
            return None

        try:
            file = await self.bot.get_file(file_id)
            if not file.file_path:
                logger.warning("Voice file has no file_path")
                return None
            audio_bytes = await self.bot.download_file(file.file_path)
            if audio_bytes:
                return audio_bytes.read()
            return None
        except Exception as e:
            logger.error(
                "Failed to download voice file",
                extra={"file_id": file_id, "error": str(e)},
                exc_info=True,
            )
            return None
