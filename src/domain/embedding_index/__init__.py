"""Embedding index domain package."""

from .interfaces import (
    ChunkRepository,
    Chunker,
    DocumentCollector,
    DocumentRepository,
    EmbeddingGateway,
    VectorStore,
)
from .value_objects import (
    ChunkingSettings,
    DocumentChunk,
    DocumentPayload,
    DocumentRecord,
    EmbeddingVector,
)

__all__ = [
    "ChunkRepository",
    "Chunker",
    "ChunkingSettings",
    "DocumentChunk",
    "DocumentCollector",
    "DocumentPayload",
    "DocumentRecord",
    "DocumentRepository",
    "EmbeddingGateway",
    "EmbeddingVector",
    "VectorStore",
]
