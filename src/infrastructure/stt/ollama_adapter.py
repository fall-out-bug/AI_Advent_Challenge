"""Whisper speech-to-text adapter implementation.

Purpose:
    Implements SpeechToTextService Protocol using Whisper STT server
    (HTTP API) for offline transcription. This is separate from LLM service
    (Mistral/Ollama for LLM, Whisper for STT).
"""

from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

import httpx

try:
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None  # type: ignore

from src.domain.voice.exceptions import SpeechToTextError
from src.domain.voice.interfaces import SpeechToTextService
from src.domain.voice.value_objects import TranscriptionResult
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.metrics.voice_metrics import (
    voice_transcription_duration_seconds,
    voice_transcriptions_total,
)

logger = get_logger(__name__)


class WhisperSpeechToTextAdapter:
    """Whisper-based speech-to-text adapter.

    Purpose:
        Transcribes audio using Whisper STT server (HTTP API).
        Separate from LLM service (Mistral/Ollama for LLM, Whisper for STT).
        Handles temp file creation and cleanup, metrics, and error handling.

    Args:
        settings: Optional settings instance (defaults to get_settings()).
        timeout: Request timeout in seconds (default 30.0).
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        timeout: float = 120.0,  # Increased timeout for Whisper model loading and transcription (especially on CPU)
    ) -> None:
        self.settings = settings or get_settings()
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._base_url = (
            f"http://{self.settings.whisper_host}:{self.settings.whisper_port}"
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def __aenter__(self) -> "WhisperSpeechToTextAdapter":
        """Async context manager entry."""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def transcribe(
        self,
        audio: bytes,
        language: str = "ru",
    ) -> TranscriptionResult:
        """Transcribe audio bytes to text using Ollama Whisper.

        Purpose:
            Saves audio bytes to temporary WAV file, sends to Ollama API,
            parses response with text and confidence, cleans up temp file.

        Args:
            audio: Raw audio bytes (PCM, WAV, OGG/OPUS).
            language: ISO language code (default "ru").

        Returns:
            TranscriptionResult with text, confidence, language, and duration_ms.

        Raises:
            SpeechToTextError: On transcription failures (network errors,
                Ollama unavailable, parsing errors).

        Example:
            >>> adapter = WhisperSpeechToTextAdapter()
            >>> result = await adapter.transcribe(audio_bytes, language="ru")
            >>> result.text
            "Сделай дайджест по каналу X"
        """
        start_time = time.time()
        temp_file_path: Optional[Path] = None

        try:
            # Create temp directory if it doesn't exist
            temp_dir = Path("/tmp/voice_agent")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Save audio bytes to temporary file
            temp_file_path = temp_dir / f"{uuid4()}.wav"

            # Convert audio to WAV if needed (using pydub if available)
            if PYDUB_AVAILABLE:
                try:
                    # Write raw bytes to temp file first
                    temp_input = temp_dir / f"{uuid4()}.tmp"
                    temp_input.write_bytes(audio)

                    # Convert to WAV using pydub
                    audio_segment = AudioSegment.from_file(str(temp_input))
                    audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
                    audio_segment.export(str(temp_file_path), format="wav")

                    # Clean up temp input file
                    temp_input.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(
                        f"Failed to convert audio with pydub, using raw bytes: {e}"
                    )
                    # Fallback: write raw bytes as WAV (assume it's already WAV)
                    temp_file_path.write_bytes(audio)
            else:
                # No pydub available, assume audio is already WAV
                temp_file_path.write_bytes(audio)

            # Calculate duration (rough estimate: 16kHz, 16-bit, mono)
            # For OGG, actual duration might differ, but this is a reasonable default
            audio_size_bytes = len(audio)
            estimated_duration_ms = int(
                (audio_size_bytes / 32000) * 1000
            )  # Rough estimate

            # Call Whisper API for transcription
            # Note: We use Ollama adapter interface but connect to Whisper server
            client = await self._get_client()
            url = f"{self._base_url}/api/transcribe"

            # Read file content first (before async operation)
            file_content = temp_file_path.read_bytes()

            # Prepare multipart form data
            files = {"file": (temp_file_path.name, file_content, "audio/wav")}
            # Whisper API expects form data with file and language
            data = {
                "language": language,
                # Model is set in Whisper server via WHISPER_MODEL env var
            }

            try:
                response = await client.post(
                    url, files=files, data=data, timeout=self.timeout
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                voice_transcriptions_total.labels(status="error").inc()
                error_text = e.response.text if e.response else str(e)
                # Check if model not found (404 or 400 with model error)
                if e.response.status_code == 404 or (
                    e.response.status_code == 400 and "model" in error_text.lower()
                ):
                    raise SpeechToTextError(
                        f"Whisper STT model '{self.settings.stt_model}' not found. "
                        f"Please check WHISPER_MODEL environment variable in whisper-stt service.",
                        audio_format="wav",
                    ) from e
                raise SpeechToTextError(
                    f"Whisper API error: {e.response.status_code} - {error_text}",
                    audio_format="wav",
                ) from e
            except httpx.RequestError as e:
                voice_transcriptions_total.labels(status="error").inc()
                error_msg = str(e) if str(e) else f"{type(e).__name__}: {e}"
                logger.error(
                    f"Network error calling Whisper API: {error_msg}",
                    extra={
                        "error_type": type(e).__name__,
                        "url": url,
                        "timeout": self.timeout,
                    },
                )
                raise SpeechToTextError(
                    f"Network error calling Whisper API: {error_msg}. "
                    "Make sure Whisper STT server is running and accessible.",
                    audio_format="wav",
                ) from e

            # Parse response
            try:
                response_json = response.json()
                text = response_json.get("text", "").strip()
                # Ollama whisper doesn't return confidence directly, estimate from response quality
                confidence = response_json.get("confidence", 0.9)  # Default fallback
                if "segments" in response_json and response_json["segments"]:
                    # Calculate average confidence from segments if available
                    segments = response_json["segments"]
                    confidences = [
                        s.get("confidence", 0.9) for s in segments if "confidence" in s
                    ]
                    if confidences:
                        confidence = sum(confidences) / len(confidences)

                if not text:
                    voice_transcriptions_total.labels(status="error").inc()
                    raise SpeechToTextError(
                        "Empty transcription result from Ollama",
                        audio_format="wav",
                    )

                result = TranscriptionResult(
                    text=text,
                    confidence=confidence,
                    language=language,
                    duration_ms=estimated_duration_ms,
                )

                duration = time.time() - start_time
                voice_transcription_duration_seconds.observe(duration)
                voice_transcriptions_total.labels(status="success").inc()

                logger.info(
                    "Voice transcription completed",
                    extra={
                        "language": language,
                        "confidence": confidence,
                        "text_length": len(text),
                        "duration_seconds": duration,
                    },
                )

                return result

            except (KeyError, ValueError, TypeError) as e:
                voice_transcriptions_total.labels(status="error").inc()
                raise SpeechToTextError(
                    f"Failed to parse Ollama response: {str(e)}",
                    audio_format="wav",
                ) from e

        finally:
            # Cleanup temp file immediately (success or error)
            if temp_file_path is not None and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as e:
                    logger.warning(
                        f"Failed to delete temp file {temp_file_path}: {e}",
                        extra={"temp_file": str(temp_file_path)},
                    )
