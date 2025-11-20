"""Domain interfaces for voice agent.

Purpose:
    Defines protocols for speech-to-text services and related abstractions.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.voice.value_objects import TranscriptionResult


@runtime_checkable
class SpeechToTextService(Protocol):
    """Protocol for speech-to-text transcription services.

    Purpose:
        Defines a canonical interface for offline STT processing,
        decoupling domain logic from specific STT implementations
        (Ollama, Vosk, etc.). Enforces offline-only operation:
        audio never leaves the host.

    Methods:
        transcribe: Transcribe audio bytes to text with confidence score.
    """

    async def transcribe(
        self,
        audio: bytes,
        language: str = "ru",
    ) -> TranscriptionResult:
        """Transcribe audio bytes to text.

        Purpose:
            Performs offline speech-to-text transcription on audio data.
            Returns transcription result with text, confidence score,
            language, and duration.

        Args:
            audio: Raw audio bytes (PCM, WAV, OGG/OPUS supported formats).
            language: ISO language code (default "ru" for Russian).

        Returns:
            TranscriptionResult with text, confidence, language, and duration_ms.

        Raises:
            SpeechToTextError: On transcription failures (decoding errors,
                model unavailable, audio format unsupported).

        Example:
            >>> service = WhisperSpeechToTextAdapter(...)
            >>> result = await service.transcribe(audio_bytes, language="ru")
            >>> result.text
            "Сделай дайджест по каналу X"
            >>> result.confidence
            0.85
        """
        ...
