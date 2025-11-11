"""Unit tests for BuildEmbeddingIndexUseCase."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import pytest

from src.application.embedding_index.dtos import IndexingRequest
from src.application.embedding_index.use_case import BuildEmbeddingIndexUseCase
from src.domain.embedding_index import (
    ChunkRepository,
    Chunker,
    ChunkingSettings,
    DocumentCollector,
    DocumentPayload,
    DocumentRecord,
    DocumentRepository,
    EmbeddingGateway,
    EmbeddingVector,
    VectorStore,
)


@dataclass
class DummyCollector(DocumentCollector):
    """Collects provided payloads."""

    payloads: Sequence[DocumentPayload]

    def collect(
        self,
        sources: Sequence[str],
        max_file_size_bytes: int,
        extra_tags: Mapping[str, str],
    ) -> Iterable[DocumentPayload]:
        return self.payloads


class DummyChunker(Chunker):
    """Chunker yielding a single chunk equal to the payload content."""

    def build_chunks(
        self,
        payload: DocumentPayload,
        settings: ChunkingSettings,
    ) -> Sequence:
        from src.domain.embedding_index.value_objects import DocumentChunk

        return [
            DocumentChunk(
                chunk_id=f"{payload.record.document_id}-0",
                document_id=payload.record.document_id,
                ordinal=0,
                text=payload.content,
                token_count=len(payload.content.split()),
                metadata={"source": payload.record.source},
            )
        ]


class DummyDocumentRepository(DocumentRepository):
    """In-memory document repository."""

    def __init__(self) -> None:
        self.records: list[DocumentRecord] = []

    def upsert_document(self, record: DocumentRecord) -> None:
        self.records.append(record)


class DummyChunkRepository(ChunkRepository):
    """In-memory chunk repository."""

    def __init__(self) -> None:
        self.chunks: dict[str, object] = {}

    def upsert_chunks(self, chunks) -> None:
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk


class DummyEmbeddingGateway(EmbeddingGateway):
    """Embedding gateway capturing batch calls."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, chunks) -> Sequence[EmbeddingVector]:
        self.calls.append([chunk.chunk_id for chunk in chunks])
        vectors = []
        for chunk in chunks:
            vectors.append(
                EmbeddingVector(
                    values=(float(len(chunk.text)),),
                    model="test-model",
                    dimension=1,
                    metadata={"chunk_id": chunk.chunk_id},
                )
            )
        return vectors


class DummyVectorStore(VectorStore):
    """Vector store capturing upsert requests."""

    def __init__(self) -> None:
        self.entries: list[tuple[Sequence, Sequence]] = []

    def upsert(self, chunks, vectors) -> None:
        self.entries.append((tuple(chunks), tuple(vectors)))


def _build_payload(doc_id: str, content: str, source: str = "docs") -> DocumentPayload:
    record = DocumentRecord(
        document_id=doc_id,
        source_path=f"/tmp/{doc_id}.md",
        source=source,
        language="ru",
        sha256="a" * 64,
        tags={"stage": "19"},
    )
    return DocumentPayload(record=record, content=content)


def test_use_case_indexes_documents_and_embeddings() -> None:
    """Ensure the use case orchestrates repositories and vector store."""
    payloads = [
        _build_payload("doc-1", "first document"),
        _build_payload("doc-2", "second"),
    ]
    collector = DummyCollector(payloads)
    chunker = DummyChunker()
    doc_repo = DummyDocumentRepository()
    chunk_repo = DummyChunkRepository()
    gateway = DummyEmbeddingGateway()
    vector_store = DummyVectorStore()
    use_case = BuildEmbeddingIndexUseCase(
        collector=collector,
        chunker=chunker,
        embedding_gateway=gateway,
        document_repository=doc_repo,
        chunk_repository=chunk_repo,
        vector_store=vector_store,
    )
    request = IndexingRequest(
        sources=["/tmp/docs"],
        chunking_settings=ChunkingSettings(chunk_size_tokens=1200, chunk_overlap_tokens=200),
        extra_tags={"language": "ru", "stage": "19"},
        batch_size=2,
    )

    result = use_case.execute(request)

    assert result.documents_indexed == 2
    assert result.chunks_indexed == 2
    assert result.embeddings_indexed == 2
    assert len(doc_repo.records) == 2
    assert len(chunk_repo.chunks) == 2
    annotated_chunk = chunk_repo.chunks["doc-1-0"]
    assert annotated_chunk.metadata["embedding_model"] == "test-model"
    assert annotated_chunk.metadata["chunk_id"] == "doc-1-0"
    assert len(vector_store.entries) == 1


def test_use_case_batches_embeddings_respecting_batch_size() -> None:
    """Ensure embedding requests honour batch size limits."""
    payloads = [
        _build_payload("doc-1", "one"),
        _build_payload("doc-2", "two"),
        _build_payload("doc-3", "three"),
    ]
    collector = DummyCollector(payloads)
    chunker = DummyChunker()
    doc_repo = DummyDocumentRepository()
    chunk_repo = DummyChunkRepository()
    gateway = DummyEmbeddingGateway()
    vector_store = DummyVectorStore()
    use_case = BuildEmbeddingIndexUseCase(
        collector=collector,
        chunker=chunker,
        embedding_gateway=gateway,
        document_repository=doc_repo,
        chunk_repository=chunk_repo,
        vector_store=vector_store,
    )
    request = IndexingRequest(
        sources=["/tmp/docs"],
        chunking_settings=ChunkingSettings(chunk_size_tokens=1200, chunk_overlap_tokens=200),
        extra_tags={"language": "ru", "stage": "19"},
        batch_size=2,
    )

    use_case.execute(request)

    assert len(gateway.calls) == 2
    assert gateway.calls[0] == ["doc-1-0", "doc-2-0"]
    assert gateway.calls[1] == ["doc-3-0"]

