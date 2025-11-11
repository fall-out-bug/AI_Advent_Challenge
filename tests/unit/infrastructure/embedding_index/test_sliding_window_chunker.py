"""Tests for SlidingWindowChunker."""

from __future__ import annotations

from src.domain.embedding_index import ChunkingSettings, DocumentPayload, DocumentRecord
from src.infrastructure.embedding_index.chunking.sliding_window_chunker import (
    SlidingWindowChunker,
)


def _build_payload(text: str) -> DocumentPayload:
    record = DocumentRecord(
        document_id="doc-1",
        source_path="/tmp/doc.md",
        source="docs",
        language="ru",
        sha256="a" * 64,
    )
    return DocumentPayload(record=record, content=text)


def test_chunker_generates_overlapping_chunks() -> None:
    """Ensure chunker respects size and overlap configuration."""
    text = " ".join(f"token{i}" for i in range(30))
    payload = _build_payload(text)
    chunker = SlidingWindowChunker()
    settings = ChunkingSettings(
        chunk_size_tokens=10,
        chunk_overlap_tokens=2,
        min_chunk_tokens=4,
    )

    chunks = chunker.build_chunks(payload=payload, settings=settings)

    assert len(chunks) == 4
    assert chunks[0].token_count == 10
    assert chunks[-1].token_count >= settings.min_chunk_tokens
    assert chunks[0].metadata["chunk_strategy"] == "sliding_window"

