"""Unit tests for RetrievalService and compatibility adapter."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

import pytest

from src.application.rag import RetrievalService, RetrievalServiceCompat
from src.domain.embedding_index import EmbeddingVector
from src.domain.rag import (
    FilterConfig,
    RerankResult,
    RetrievedChunk,
    RelevanceFilterService,
    RerankerService,
    VectorSearchService,
)


def _build_chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        text=f"chunk text {chunk_id}",
        similarity_score=score,
        source_path="/docs/specs/architecture.md",
        metadata={},
    )


@dataclass
class StubVectorSearch(VectorSearchService):
    """Simple stub returning predefined chunks."""

    chunks: Sequence[RetrievedChunk]

    def __post_init__(self) -> None:
        self.calls: list[dict] = []

    def search(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[RetrievedChunk]:
        self.calls.append(
            {"vector": query_vector, "top_k": top_k, "threshold": score_threshold}
        )
        return self.chunks


@dataclass
class StubFilter(RelevanceFilterService):
    """Stub filter that records calls and returns predefined chunks."""

    filtered: Sequence[RetrievedChunk]

    def __post_init__(self) -> None:
        self.calls: list[dict] = []

    def filter_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
        threshold: float,
        top_k: int,
    ) -> Sequence[RetrievedChunk]:
        self.calls.append(
            {"chunks": chunks, "threshold": threshold, "top_k": top_k}
        )
        return self.filtered


@dataclass
class StubReranker(RerankerService):
    """Stub reranker returning deterministic results."""

    reordered: Sequence[RetrievedChunk]
    scores: dict[str, float]
    should_raise: bool = False

    def __post_init__(self) -> None:
        self.calls: list[dict] = []

    async def rerank(
        self,
        query: str,
        chunks: Sequence[RetrievedChunk],
    ) -> RerankResult:
        if self.should_raise:
            raise RuntimeError("reranker failure")
        self.calls.append({"query": query, "chunks": chunks})
        return RerankResult(
            chunks=self.reordered,
            rerank_scores=self.scores,
            strategy="llm",
            latency_ms=42,
            reasoning="stub",
        )


def _build_vector() -> EmbeddingVector:
    return EmbeddingVector(
        values=(0.1, 0.2),
        model="all-MiniLM-L6-v2",
        dimension=2,
    )


@pytest.mark.asyncio
async def test_retrieval_service_applies_filter_and_limits_results() -> None:
    """Service should fetch headroom, apply filter, and limit to top_k."""
    raw_chunks = [_build_chunk("chunk-1", 0.9), _build_chunk("chunk-2", 0.7)]
    filtered_chunks = raw_chunks[:1]
    vector_search = StubVectorSearch(chunks=raw_chunks)
    filter_stub = StubFilter(filtered=filtered_chunks)
    service = RetrievalService(
        vector_search=vector_search,
        relevance_filter=filter_stub,
        reranker=None,
    )
    config = FilterConfig(score_threshold=0.3, top_k=1)

    result = await service.retrieve(
        query_text="Что такое MapReduce?",
        query_vector=_build_vector(),
        filter_config=config,
    )

    assert result == filtered_chunks
    assert vector_search.calls[0]["top_k"] == config.top_k * 2
    assert vector_search.calls[0]["threshold"] == 0.0
    assert filter_stub.calls[0]["threshold"] == config.score_threshold
    assert filter_stub.calls[0]["top_k"] == config.top_k


@pytest.mark.asyncio
async def test_retrieval_service_invokes_reranker_when_enabled() -> None:
    """Reranker should override order when enabled."""
    raw_chunks = [
        _build_chunk("chunk-1", 0.9),
        _build_chunk("chunk-2", 0.8),
    ]
    filtered_chunks = list(raw_chunks)
    reranked_chunks = list(reversed(filtered_chunks))
    vector_search = StubVectorSearch(chunks=raw_chunks)
    filter_stub = StubFilter(filtered=filtered_chunks)
    reranker = StubReranker(
        reordered=reranked_chunks,
        scores={"chunk-1": 0.55, "chunk-2": 0.91},
    )
    service = RetrievalService(
        vector_search=vector_search,
        relevance_filter=filter_stub,
        reranker=reranker,
    )
    config = FilterConfig.with_reranking(
        score_threshold=0.3,
        top_k=2,
        strategy="llm",
    )

    result = await service.retrieve(
        query_text="Что такое MapReduce?",
        query_vector=_build_vector(),
        filter_config=config,
    )

    assert list(result) == reranked_chunks
    assert reranker.calls and reranker.calls[0]["query"].startswith("Что такое")


@pytest.mark.asyncio
async def test_retrieval_service_falls_back_when_reranker_fails() -> None:
    """On reranker failure the service should return filtered chunks."""
    raw_chunks = [
        _build_chunk("chunk-1", 0.9),
        _build_chunk("chunk-2", 0.7),
    ]
    filtered_chunks = raw_chunks[:2]
    vector_search = StubVectorSearch(chunks=raw_chunks)
    filter_stub = StubFilter(filtered=filtered_chunks)
    reranker = StubReranker(
        reordered=filtered_chunks,
        scores={"chunk-1": 0.8, "chunk-2": 0.5},
        should_raise=True,
    )
    service = RetrievalService(
        vector_search=vector_search,
        relevance_filter=filter_stub,
        reranker=reranker,
    )
    config = FilterConfig.with_reranking(score_threshold=0.3, top_k=2)

    result = await service.retrieve(
        query_text="Что такое MapReduce?",
        query_vector=_build_vector(),
        filter_config=config,
    )

    assert list(result) == list(filtered_chunks)


@pytest.mark.asyncio
async def test_retrieval_service_without_filter_slices_headroom() -> None:
    """Without filter the service should fall back to top_k slicing."""
    raw_chunks = [
        _build_chunk("chunk-1", 0.9),
        _build_chunk("chunk-2", 0.8),
        _build_chunk("chunk-3", 0.7),
    ]
    vector_search = StubVectorSearch(chunks=raw_chunks)
    service = RetrievalService(
        vector_search=vector_search,
        relevance_filter=None,
        reranker=None,
    )
    config = FilterConfig(score_threshold=0.0, top_k=2)

    result = await service.retrieve(
        query_text="Что такое MapReduce?",
        query_vector=_build_vector(),
        filter_config=config,
    )

    assert list(result) == raw_chunks[: config.top_k]


def test_retrieval_service_compat_runs_async_pipeline() -> None:
    """Compatibility wrapper should expose synchronous API."""
    raw_chunks = [_build_chunk("chunk-1", 0.9)]
    vector_search = StubVectorSearch(chunks=raw_chunks)
    filter_stub = StubFilter(filtered=raw_chunks)
    reranker = StubReranker(reordered=raw_chunks, scores={"chunk-1": 0.95})
    service = RetrievalService(
        vector_search=vector_search,
        relevance_filter=filter_stub,
        reranker=reranker,
    )
    compat = RetrievalServiceCompat(service=service)

    result = compat.retrieve(
        query_vector=_build_vector(),
        top_k=1,
        score_threshold=0.3,
    )

    assert list(result) == raw_chunks
