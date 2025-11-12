"""Tests for ThresholdFilterAdapter."""

from __future__ import annotations

import pytest

from src.domain.rag import RetrievedChunk
from src.infrastructure.rag.threshold_filter_adapter import ThresholdFilterAdapter


def _build_chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        text=f"text {chunk_id}",
        similarity_score=score,
        source_path="/docs/specs/architecture.md",
        metadata={},
    )


def test_threshold_filter_edge_cases() -> None:
    """Adapter should handle empty input and all-below-threshold lists."""
    adapter = ThresholdFilterAdapter()

    assert adapter.filter_chunks([], threshold=0.5, top_k=5) == []

    chunks = [_build_chunk("chunk-1", 0.2), _build_chunk("chunk-2", 0.3)]
    assert adapter.filter_chunks(chunks, threshold=0.9, top_k=5) == []


def test_threshold_filter_preserves_order_and_limits_top_k() -> None:
    """Filtering should preserve order and enforce top_k limit."""
    adapter = ThresholdFilterAdapter()
    chunks = [
        _build_chunk("chunk-1", 0.9),
        _build_chunk("chunk-2", 0.8),
        _build_chunk("chunk-3", 0.7),
    ]

    result = adapter.filter_chunks(chunks, threshold=0.7, top_k=2)

    assert [chunk.chunk_id for chunk in result] == ["chunk-1", "chunk-2"]


@pytest.mark.parametrize("threshold", (-0.1, 1.1))
def test_threshold_filter_invalid_threshold_raises(threshold: float) -> None:
    """Validation should fail for thresholds outside [0.0, 1.0]."""
    adapter = ThresholdFilterAdapter()

    with pytest.raises(ValueError, match="threshold"):
        adapter.filter_chunks([_build_chunk("chunk-1", 0.5)], threshold, top_k=3)


def test_threshold_filter_invalid_top_k_raises() -> None:
    """Validation should fail for top_k < 1."""
    adapter = ThresholdFilterAdapter()

    with pytest.raises(ValueError, match="top_k"):
        adapter.filter_chunks([_build_chunk("chunk-1", 0.5)], threshold=0.3, top_k=0)
