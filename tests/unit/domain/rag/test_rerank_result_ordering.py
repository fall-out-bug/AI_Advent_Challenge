"""Tests for RerankResult value object."""

from __future__ import annotations

import pytest

from src.domain.rag import RerankResult, RetrievedChunk


def _build_chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        text=f"text for {chunk_id}",
        similarity_score=score,
        source_path="/docs/specs/architecture.md",
        metadata={},
    )


def test_rerank_result_validates_inputs() -> None:
    """Value object should hold chunks, scores, and metadata."""
    chunk_a = _build_chunk("chunk-a", 0.8)
    chunk_b = _build_chunk("chunk-b", 0.6)
    result = RerankResult(
        chunks=(chunk_a, chunk_b),
        rerank_scores={"chunk-a": 0.91, "chunk-b": 0.55},
        strategy="llm",
        latency_ms=120,
        reasoning="Chunk A matches the query best.",
    )

    assert result.chunks[0] == chunk_a
    assert result.chunks[1] == chunk_b
    assert result.rerank_scores["chunk-a"] == pytest.approx(0.91)
    assert result.reasoning == "Chunk A matches the query best."


def test_rerank_result_missing_score_raises() -> None:
    """Each chunk must have a corresponding rerank score."""
    chunk = _build_chunk("chunk-a", 0.8)

    with pytest.raises(ValueError, match="Missing rerank_score"):
        RerankResult(
            chunks=(chunk,),
            rerank_scores={},
            strategy="llm",
            latency_ms=50,
        )


def test_rerank_result_invalid_strategy_raises() -> None:
    """Strategy must be one of the supported options."""
    chunk = _build_chunk("chunk-a", 0.8)

    with pytest.raises(ValueError, match="strategy"):
        RerankResult(
            chunks=(chunk,),
            rerank_scores={"chunk-a": 0.9},
            strategy="bm25",
            latency_ms=75,
        )


def test_rerank_result_negative_latency_raises() -> None:
    """Latency must be non-negative."""
    chunk = _build_chunk("chunk-a", 0.8)

    with pytest.raises(ValueError, match="latency_ms"):
        RerankResult(
            chunks=(chunk,),
            rerank_scores={"chunk-a": 0.9},
            strategy="llm",
            latency_ms=-1,
        )


def test_rerank_result_requires_descending_scores() -> None:
    """Chunks must be ordered by descending rerank score."""
    chunk_a = _build_chunk("chunk-a", 0.8)
    chunk_b = _build_chunk("chunk-b", 0.6)

    with pytest.raises(ValueError, match="must be ordered by descending"):
        RerankResult(
            chunks=(chunk_b, chunk_a),
            rerank_scores={"chunk-a": 0.9, "chunk-b": 0.4},
            strategy="llm",
            latency_ms=100,
        )
