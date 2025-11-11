"""Integration smoke tests for VectorSearchAdapter."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, Sequence

import pytest

from src.domain.embedding_index import DocumentChunk, DocumentRecord, EmbeddingVector
from src.infrastructure.rag import VectorSearchAdapter

pytestmark = pytest.mark.integration


def _load_fallback_index() -> tuple[Path, dict[str, object]]:
    path = Path("var/indices/embedding_index_v1.pkl")
    if not path.exists():
        pytest.skip("FAISS fallback index not found; run EP19 indexer first.")
    try:
        with path.open("rb") as handle:
            vectors = pickle.load(handle)
    except (OSError, pickle.PickleError) as error:
        pytest.skip(f"Failed to load fallback index: {error}")
    if not isinstance(vectors, dict) or not vectors:
        pytest.skip("Fallback index is empty or malformed.")
    return path, vectors


class _StubChunkRepository:
    """Stub repository that synthesises chunks for requested IDs."""

    def __init__(self, embeddings: Dict[str, EmbeddingVector]) -> None:
        self._embeddings = embeddings

    def upsert_chunks(self, chunks) -> None:  # pragma: no cover - not used
        raise NotImplementedError

    def get_chunks_by_ids(self, chunk_ids: Sequence[str]) -> Sequence[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for chunk_id in chunk_ids:
            embedding = self._embeddings.get(chunk_id)
            if embedding is None:
                continue
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id="stub-doc",
                    ordinal=0,
                    text=f"Stub text for {chunk_id}",
                    token_count=len(embedding.values),
                    metadata={},
                )
            )
        return chunks


class _StubDocumentRepository:
    """Stub repository returning static document metadata."""

    def __init__(self) -> None:
        self._record = DocumentRecord(
            document_id="stub-doc",
            source_path="/tmp/stub.md",
            source="docs",
            language="ru",
            sha256="a" * 64,
        )

    def upsert_document(self, record):  # pragma: no cover - not used
        raise NotImplementedError

    def get_document_by_id(self, document_id: str) -> DocumentRecord | None:
        return self._record if document_id == self._record.document_id else None


def test_vector_search_adapter_returns_chunks_from_faiss() -> None:
    """Ensure adapter can retrieve chunks using FAISS fallback embeddings."""
    fallback_path, vectors = _load_fallback_index()
    first_chunk_id, embedding = next(iter(vectors.items()))
    if not isinstance(embedding, EmbeddingVector):
        pytest.skip("Fallback index entries are not EmbeddingVector instances.")

    repository = _StubChunkRepository(vectors)
    document_repository = _StubDocumentRepository()
    adapter = VectorSearchAdapter(
        chunk_repository=repository,
        document_repository=document_repository,
        fallback_index_path=fallback_path,
    )

    results = adapter.search(
        query_vector=embedding,
        top_k=5,
        score_threshold=0.0,
    )

    assert results, "Expected at least one chunk from FAISS fallback."

    chunk_ids = [chunk.chunk_id for chunk in results]
    assert first_chunk_id in chunk_ids, "Expected known chunk ID in search results."

    chunk = results[chunk_ids.index(first_chunk_id)]
    assert chunk.text.strip(), "Retrieved chunk should contain text content."
    assert (
        chunk.source_path == "/tmp/stub.md"
    ), "Retrieved chunk should expose source_path from document repository."
