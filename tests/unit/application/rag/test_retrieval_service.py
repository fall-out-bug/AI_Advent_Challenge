"""Unit tests for RetrievalService."""

from __future__ import annotations

from typing import List

from src.application.rag import RetrievalService
from src.domain.embedding_index import EmbeddingVector
from src.domain.rag import RetrievedChunk, VectorSearchService


class StubVectorSearch(VectorSearchService):
    """Simple stub returning predefined chunks."""

    def __init__(self, chunks: List[RetrievedChunk]) -> None:
        self._chunks = chunks
        self.calls: list[dict] = []

    def search(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> List[RetrievedChunk]:
        self.calls.append(
            {"vector": query_vector, "top_k": top_k, "threshold": score_threshold}
        )
        return self._chunks


def _build_chunk(chunk_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        text="chunk text",
        similarity_score=score,
        source_path="/docs/specs/architecture.md",
        metadata={},
    )


def test_retrieval_service_returns_chunks() -> None:
    """Service should return the chunks from vector search."""
    chunks = [_build_chunk("chunk-1", 0.9), _build_chunk("chunk-2", 0.85)]
    stub = StubVectorSearch(chunks)
    service = RetrievalService(vector_search=stub)
    query_vector = EmbeddingVector(
        values=(0.1, 0.2),
        model="all-MiniLM-L6-v2",
        dimension=2,
    )

    result = service.retrieve(
        query_vector=query_vector,
        top_k=5,
        score_threshold=0.3,
    )

    assert result == chunks
    assert stub.calls and stub.calls[0]["top_k"] == 5
