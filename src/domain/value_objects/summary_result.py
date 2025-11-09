"""Value objects for summarization results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SummaryResult:
    """Result of text summarization.

    Purpose:
        Represents the output of a summarization operation
        with metadata about the process.

    Args:
        text: Summary text content.
        sentences_count: Number of sentences in summary.
        method: Summarization method used ("direct" | "map_reduce").
        confidence: Confidence score (0.0-1.0) if available.
        metadata: Additional metadata (duration, token counts, etc.).
    """

    text: str
    sentences_count: int
    method: str  # "direct" | "map_reduce"
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate result data."""
        if not self.text or not self.text.strip():
            raise ValueError("Summary text cannot be empty")
        if self.sentences_count < 0:
            raise ValueError("Sentence count cannot be negative")
        if self.method not in ("direct", "map_reduce"):
            raise ValueError(f"Unknown method: {self.method}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
