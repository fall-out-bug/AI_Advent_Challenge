"""Data transfer objects for the embedding index use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from src.domain.embedding_index import ChunkingSettings


@dataclass(frozen=True)
class IndexingRequest:
    """Embedding index request parameters.

    Purpose:
        Capture configuration supplied by presentation layer components
        (CLI/API) when triggering the indexing pipeline.

    Args:
        sources: Absolute paths of directories/files to index.
        chunking_settings: Chunk window configuration.
        extra_tags: Additional metadata tags to attach to documents/chunks.
        max_file_size_bytes: Maximum allowed file size for ingestion.
        batch_size: Number of chunks processed per embedding request.

    Raises:
        ValueError: If validation fails (e.g., empty sources, non-positive
            batch size, or negative max file size).

    Example:
        >>> IndexingRequest(
        ...     sources=('/tmp/docs',),
        ...     chunking_settings=ChunkingSettings(
        ...         chunk_size_tokens=1200,
        ...         chunk_overlap_tokens=200,
        ...     ),
        ...     extra_tags={'stage': '19', 'language': 'ru'},
        ... )
        IndexingRequest(...)
    """

    sources: Sequence[str]
    chunking_settings: ChunkingSettings
    extra_tags: Mapping[str, str]
    max_file_size_bytes: int = 20 * 1024 * 1024
    batch_size: int = 32

    def __post_init__(self) -> None:
        """Validate request attributes.

        Purpose:
            Ensure runtime inputs conform to business rules prior to execution.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: If validation fails.

        Example:
            >>> IndexingRequest(
            ...     sources=('docs',),
            ...     chunking_settings=ChunkingSettings(
            ...         chunk_size_tokens=1200,
            ...         chunk_overlap_tokens=200,
            ...     ),
            ...     extra_tags={'stage': '19', 'language': 'ru'},
            ...     batch_size=0,
            ... )
            Traceback (most recent call last):
            ...
            ValueError: batch_size must be positive.
        """
        if not self.sources:
            raise ValueError("sources cannot be empty.")
        if any(not source or not source.strip() for source in self.sources):
            raise ValueError("sources entries cannot be blank.")
        if self.max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be positive.")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive.")


@dataclass(frozen=True)
class IndexingResult:
    """Embedding index execution summary.

    Purpose:
        Convey pipeline statistics back to the caller for logging/reporting.

    Args:
        documents_indexed: Number of documents processed.
        chunks_indexed: Number of chunks stored.
        embeddings_indexed: Number of embeddings written to the vector store.

    Example:
        >>> IndexingResult(documents_indexed=1, chunks_indexed=10, embeddings_indexed=10)
        IndexingResult(documents_indexed=1, chunks_indexed=10, embeddings_indexed=10)
    """

    documents_indexed: int
    chunks_indexed: int
    embeddings_indexed: int
