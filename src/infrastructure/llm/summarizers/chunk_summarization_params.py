"""Dataclass for map-reduce chunk summarization parameters.

Purpose:
    Provides a structured way to pass parameters to chunk summarization
    methods, avoiding signature drift and parameter mismatches.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.summarization_context import SummarizationContext
from src.infrastructure.llm.chunking.semantic_chunker import TextChunk


@dataclass
class ChunkSummarizationParams:
    """Parameters for summarizing a single chunk in Map-Reduce phase.

    Purpose:
        Encapsulates all parameters needed for chunk summarization,
        providing a stable interface and avoiding signature drift.

    Args:
        chunk: TextChunk to summarize.
        max_sentences: Maximum sentences for this chunk summary.
        language: Target language for summary (default: "ru").
        context: Optional summarization context for channel/domain info.
    """

    chunk: TextChunk
    max_sentences: int
    language: str = "ru"
    context: SummarizationContext | None = None

    def __post_init__(self) -> None:
        """Validate parameters."""
        if self.max_sentences < 1:
            raise ValueError("max_sentences must be at least 1")
        if self.language not in ("ru", "en"):
            raise ValueError(f"Unsupported language: {self.language}")

