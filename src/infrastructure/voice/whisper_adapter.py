"""Whisper STT adapter implementation.

Purpose:
    Implements SpeechToTextAdapter protocol using Whisper STT HTTP API.
"""

from typing import Optional

import httpx

from src.domain.interfaces.voice import SpeechToTextAdapter
from src.domain.value_objects.transcription import Transcription
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger

logger = get_logger("voice.whisper_adapter")


class WhisperSpeechToTextAdapter:
    """Whisper STT adapter for speech-to-text transcription.

    Purpose:
        Implements SpeechToTextAdapter protocol by calling Whisper STT HTTP API.
        Handles HTTP requests, error handling, and response parsing.

    Args:
        host: Whisper STT service host (default: from settings).
        port: Whisper STT service port (default: from settings).
        model: Whisper model name (default: from settings).
        timeout: HTTP request timeout in seconds (default: 60.0).
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        settings = get_settings()
        self.host = host or settings.whisper_host
        self.port = port or settings.whisper_port
        self.model = model or settings.stt_model
        self.timeout = timeout
        self.base_url = f"http://{self.host}:{self.port}"

        logger.info(
            "WhisperSpeechToTextAdapter initialized",
            extra={
                "host": self.host,
                "port": self.port,
                "model": self.model,
                "base_url": self.base_url,
            },
        )

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "ru",
        model: Optional[str] = None,
    ) -> Transcription:
        """Transcribe audio bytes to text.

        Purpose:
            Sends audio bytes to Whisper STT API, receives transcription,
            and returns Transcription value object.

        Args:
            audio_bytes: Raw audio data bytes.
            language: Language code (default: "ru" for Russian).
            model: Optional model override (uses instance model if None).

        Returns:
            Transcription value object with text, confidence, language, duration.

        Raises:
            RuntimeError: If transcription fails or API returns error.

        Example:
            >>> adapter = WhisperSpeechToTextAdapter()
            >>> transcription = await adapter.transcribe(
            ...     audio_bytes=b"...",
            ...     language="ru",
            ... )
            >>> transcription.text
            'Привет, мир!'
        """
        logger.debug(
            "Transcribing audio",
            extra={
                "audio_size_bytes": len(audio_bytes),
                "language": language,
                "model": model or self.model,
            },
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare form data
                files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                data = {
                    "language": language,
                }
                if model:
                    data["model"] = model

                # Send request to Whisper STT API
                response = await client.post(
                    f"{self.base_url}/api/transcribe",
                    files=files,
                    data=data,
                )

                response.raise_for_status()
                result = response.json()

                transcription = Transcription(
                    text=result.get("text", ""),
                    confidence=result.get("confidence", 0.85),
                    language=result.get("language", language),
                    duration_ms=result.get("duration_ms", 0),
                    segments=result.get("segments", []),
                )

                logger.info(
                    "Audio transcribed successfully",
                    extra={
                        "text_length": len(transcription.text),
                        "confidence": transcription.confidence,
                        "language": transcription.language,
                        "duration_ms": transcription.duration_ms,
                    },
                )

                return transcription

        except httpx.HTTPStatusError as e:
            logger.error(
                "Whisper STT API error",
                extra={
                    "status_code": e.response.status_code,
                    "error": str(e),
                },
            )
            raise RuntimeError(
                f"Whisper STT API error: {e.response.status_code}"
            ) from e

        except httpx.RequestError as e:
            logger.error(
                "Whisper STT request error",
                extra={
                    "error": str(e),
                },
            )
            raise RuntimeError(f"Whisper STT request failed: {str(e)}") from e

        except Exception as e:
            logger.error(
                "Unexpected transcription error",
                extra={
                    "error": str(e),
                },
                exc_info=True,
            )
            raise RuntimeError(f"Transcription failed: {str(e)}") from e
