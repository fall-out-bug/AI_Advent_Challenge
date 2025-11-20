"""Fallback STT adapter with automatic fallback between Ollama and Vosk.

Purpose:
    Wraps Ollama and Vosk adapters, automatically falling back to Vosk
    if Ollama fails (e.g., model not found, network error).
"""

from __future__ import annotations

from typing import Optional

from src.domain.voice.exceptions import SpeechToTextError
from src.domain.voice.interfaces import SpeechToTextService
from src.domain.voice.value_objects import TranscriptionResult
from src.infrastructure.logging import get_logger
from src.infrastructure.stt.ollama_adapter import WhisperSpeechToTextAdapter
from src.infrastructure.stt.vosk_adapter import VoskSpeechToTextAdapter

logger = get_logger("voice.fallback_stt")


class FallbackSTTAdapter:
    """STT adapter with automatic fallback between Whisper and Vosk.

    Purpose:
        Tries Whisper first, falls back to Vosk if Whisper fails.
        Enables graceful degradation when Whisper service is unavailable.

    Args:
        whisper_adapter: Optional Whisper adapter (creates new if None).
        vosk_adapter: Optional Vosk adapter (creates new if None).
        prefer_whisper: If True, prefer Whisper over Vosk (default True).
    """

    def __init__(
        self,
        whisper_adapter: Optional[WhisperSpeechToTextAdapter] = None,
        vosk_adapter: Optional[VoskSpeechToTextAdapter] = None,
        prefer_whisper: bool = True,
    ) -> None:
        self.whisper_adapter = whisper_adapter
        self.vosk_adapter = vosk_adapter
        self.prefer_whisper = prefer_whisper
        self._whisper_failed = False  # Track if Whisper has failed

    async def transcribe(
        self,
        audio: bytes,
        language: str = "ru",
    ) -> TranscriptionResult:
        """Transcribe audio with automatic fallback.

        Purpose:
            Tries primary adapter (Ollama), falls back to secondary (Vosk)
            if primary fails.

        Args:
            audio: Raw audio bytes.
            language: ISO language code (default "ru").

        Returns:
            TranscriptionResult with text, confidence, language, duration_ms.

        Raises:
            SpeechToTextError: If both adapters fail.
        """
        # Try Whisper first if preferred and not previously failed
        if self.prefer_whisper and self.whisper_adapter and not self._whisper_failed:
            try:
                result = await self.whisper_adapter.transcribe(audio, language)
                logger.debug("STT transcription succeeded via Whisper")
                return result
            except SpeechToTextError as e:
                # Check if it's a model not found error
                error_msg = str(e).lower()
                if "model" in error_msg and (
                    "not found" in error_msg or "404" in error_msg
                ):
                    logger.warning(
                        f"Whisper model not found, will use Vosk for future requests: {e}"
                    )
                    self._whisper_failed = True  # Don't try Whisper again
                else:
                    logger.warning(
                        f"Whisper transcription failed: {e}. Trying Vosk fallback."
                    )
                # Continue to Vosk fallback
            except Exception as e:
                logger.warning(f"Whisper adapter error: {e}. Trying Vosk fallback.")
                # Continue to Vosk fallback

        # Try Vosk fallback
        if self.vosk_adapter:
            try:
                result = await self.vosk_adapter.transcribe(audio, language)
                logger.info("STT transcription succeeded via Vosk (fallback)")
                return result
            except Exception as e:
                logger.error(f"Vosk transcription also failed: {e}")
                raise SpeechToTextError(
                    f"Both Whisper and Vosk failed. Last error: {str(e)}",
                    audio_format="wav",
                ) from e

        # If Vosk adapter not available, raise error
        if self.whisper_adapter:
            raise SpeechToTextError(
                "Whisper failed and Vosk adapter not available. "
                "Please install Vosk: pip install vosk pydub, "
                "or start whisper-stt service",
                audio_format="wav",
            )

        raise SpeechToTextError(
            "No STT adapters available. "
            "Please start Whisper STT service or install Vosk.",
            audio_format="wav",
        )
