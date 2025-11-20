"""Vosk speech-to-text adapter implementation (CPU fallback).

Purpose:
    Implements SpeechToTextService Protocol using Vosk library
    for CPU-only environments without GPU/Ollama support.
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.domain.voice.exceptions import SpeechToTextError
from src.domain.voice.interfaces import SpeechToTextService
from src.domain.voice.value_objects import TranscriptionResult
from src.infrastructure.logging import get_logger
from src.infrastructure.metrics.voice_metrics import (
    voice_transcription_duration_seconds,
    voice_transcriptions_total,
)

logger = get_logger(__name__)

try:
    import vosk
    from pydub import AudioSegment

    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    vosk = None  # type: ignore
    AudioSegment = None  # type: ignore


class VoskSpeechToTextAdapter:
    """Vosk-based speech-to-text adapter (CPU fallback).

    Purpose:
        Transcribes audio using Vosk library for CPU-only environments.
        Requires Vosk model files to be installed locally.

    Args:
        model_path: Path to Vosk model directory (default "/usr/share/vosk-model-ru").
        sample_rate: Audio sample rate (default 16000).
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        sample_rate: int = 16000,
    ) -> None:
        if not VOSK_AVAILABLE:
            raise ImportError(
                "Vosk is not available. Install with: pip install vosk pydub"
            )

        self.model_path = model_path or "/usr/share/vosk-model-ru"
        self.sample_rate = sample_rate
        self._model: Optional[vosk.Model] = None
        self._recognizer: Optional[vosk.KaldiRecognizer] = None

    def _load_model(self) -> None:
        """Load Vosk model (lazy initialization)."""
        if self._model is None:
            model_path = Path(self.model_path)
            if not model_path.exists():
                raise SpeechToTextError(
                    f"Vosk model not found at {self.model_path}. "
                    "Please install a Vosk model (e.g., vosk-model-small-ru-0.22).",
                    audio_format="wav",
                )

            try:
                self._model = vosk.Model(str(model_path))
                self._recognizer = vosk.KaldiRecognizer(self._model, self.sample_rate)
                self._recognizer.SetWords(True)  # Enable word-level confidence
            except Exception as e:
                raise SpeechToTextError(
                    f"Failed to load Vosk model: {str(e)}",
                    audio_format="wav",
                ) from e

    async def transcribe(
        self,
        audio: bytes,
        language: str = "ru",
    ) -> TranscriptionResult:
        """Transcribe audio bytes to text using Vosk.

        Purpose:
            Converts audio bytes to WAV format, processes with Vosk,
            extracts text and confidence from recognition result.

        Args:
            audio: Raw audio bytes (PCM, WAV, OGG/OPUS).
            language: ISO language code (default "ru", ignored by Vosk - uses model language).

        Returns:
            TranscriptionResult with text, confidence, language, and duration_ms.

        Raises:
            SpeechToTextError: On transcription failures (model not found,
                audio conversion errors, recognition failures).
        """
        start_time = time.time()
        temp_file_path: Optional[Path] = None

        try:
            self._load_model()

            # Create temp directory if it doesn't exist
            temp_dir = Path("/tmp/voice_agent")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Save audio bytes to temporary file
            temp_file_path = temp_dir / f"{uuid4()}.wav"

            # Convert audio to WAV format with correct sample rate
            try:
                # Write raw bytes to temp file first
                temp_input = temp_dir / f"{uuid4()}.tmp"
                temp_input.write_bytes(audio)

                # Convert to WAV using pydub
                audio_segment = AudioSegment.from_file(str(temp_input))
                # Convert to mono, set sample rate
                audio_segment = audio_segment.set_channels(1).set_frame_rate(
                    self.sample_rate
                )
                audio_segment.export(str(temp_file_path), format="wav")

                # Clean up temp input file
                temp_input.unlink(missing_ok=True)

            except Exception as e:
                logger.warning(
                    f"Failed to convert audio with pydub, using raw bytes: {e}"
                )
                # If conversion fails, assume audio is already WAV
                temp_file_path.write_bytes(audio)

            # Read WAV file for Vosk processing
            with open(temp_file_path, "rb") as f:
                wav_data = f.read()

            # Skip WAV header (44 bytes)
            audio_data = wav_data[44:]

            # Process audio with Vosk
            text_parts = []
            confidences = []

            if self._recognizer is None:
                raise SpeechToTextError(
                    "Vosk recognizer not initialized",
                    audio_format="wav",
                )

            # Process audio in chunks
            chunk_size = 4000  # Vosk recommended chunk size
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i : i + chunk_size]
                if self._recognizer.AcceptWaveform(chunk):
                    result_json = self._recognizer.Result()
                    import json

                    result = json.loads(result_json)
                    if "text" in result and result["text"]:
                        text_parts.append(result["text"])
                        # Extract confidence if available
                        if "result" in result:
                            for word in result["result"]:
                                if "conf" in word:
                                    confidences.append(word["conf"])

            # Get final result
            final_result_json = self._recognizer.FinalResult()
            import json

            final_result = json.loads(final_result_json)
            if "text" in final_result and final_result["text"]:
                text_parts.append(final_result["text"])
                if "result" in final_result:
                    for word in final_result["result"]:
                        if "conf" in word:
                            confidences.append(word["conf"])

            # Combine text parts
            text = " ".join(text_parts).strip()

            if not text:
                voice_transcriptions_total.labels(status="error").inc()
                raise SpeechToTextError(
                    "Empty transcription result from Vosk",
                    audio_format="wav",
                )

            # Calculate average confidence
            confidence = sum(confidences) / len(confidences) if confidences else 0.85

            # Estimate duration
            duration_ms = int((len(audio_data) / (self.sample_rate * 2)) * 1000)

            result = TranscriptionResult(
                text=text,
                confidence=confidence,
                language=language,
                duration_ms=duration_ms,
            )

            duration = time.time() - start_time
            voice_transcription_duration_seconds.observe(duration)
            voice_transcriptions_total.labels(status="success").inc()

            logger.info(
                "Voice transcription completed (Vosk)",
                extra={
                    "language": language,
                    "confidence": confidence,
                    "text_length": len(text),
                    "duration_seconds": duration,
                },
            )

            return result

        except SpeechToTextError:
            voice_transcriptions_total.labels(status="error").inc()
            raise
        except Exception as e:
            voice_transcriptions_total.labels(status="error").inc()
            raise SpeechToTextError(
                f"Vosk transcription failed: {str(e)}",
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
