"""Embedding index domain interfaces."""

from __future__ import annotations

from typing import Iterable, Mapping, Protocol, Sequence

from .value_objects import (
    ChunkingSettings,
    DocumentChunk,
    DocumentPayload,
    DocumentRecord,
    EmbeddingVector,
)


class DocumentCollector(Protocol):
    """Protocol for document collection adapters.

    Purpose:
        Abstract filesystem or external sources that emit document payloads.
    """

    def collect(
        self,
        sources: Sequence[str],
        max_file_size_bytes: int,
        extra_tags: Mapping[str, str],
    ) -> Iterable[DocumentPayload]:
        """Yield document payloads ready for preprocessing."""


class Chunker(Protocol):
    """Protocol for chunk generation services."""

    def build_chunks(
        self,
        payload: DocumentPayload,
        settings: ChunkingSettings,
    ) -> Sequence[DocumentChunk]:
        """Split a document payload into ordered chunks."""


class EmbeddingGateway(Protocol):
    """Protocol for embedding API adapters."""

    def embed(self, chunks: Sequence[DocumentChunk]) -> Sequence[EmbeddingVector]:
        """Generate embeddings for the supplied chunks."""


class DocumentRepository(Protocol):
    """Protocol for document metadata persistence."""

    def upsert_document(self, record: DocumentRecord) -> None:
        """Insert or update document metadata."""


class ChunkRepository(Protocol):
    """Protocol for chunk persistence."""

    def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        """Insert or update document chunks."""


class VectorStore(Protocol):
    """Protocol for vector index persistence."""

    def upsert(
        self,
        chunks: Sequence[DocumentChunk],
        vectors: Sequence[EmbeddingVector],
    ) -> None:
        """Insert or update embedding vectors for the given chunks."""
