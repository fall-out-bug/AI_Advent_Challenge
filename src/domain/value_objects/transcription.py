"""Transcription value object.

Purpose:
    Represents a speech-to-text transcription result with metadata.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Transcription:
    """Transcription value object.

    Purpose:
        Represents a transcribed audio segment with text, confidence,
        language, duration, and optional segment details.

    Attributes:
        text: Transcribed text content.
        confidence: Confidence score (0.0 to 1.0).
        language: Detected language code.
        duration_ms: Audio duration in milliseconds.
        segments: Optional list of segment details.

    Example:
        >>> transcription = Transcription(
        ...     text="Привет, мир!",
        ...     confidence=0.95,
        ...     language="ru",
        ...     duration_ms=2000,
        ... )
        >>> transcription.text
        'Привет, мир!'
    """

    text: str
    confidence: float
    language: str
    duration_ms: int
    segments: list[dict] | None = None

