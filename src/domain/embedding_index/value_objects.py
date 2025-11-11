"""Embedding index value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Tuple


@dataclass(frozen=True)
class DocumentRecord:
    """Immutable document metadata for the embedding index.

    Purpose:
        Represent canonical metadata about a document slated for indexing.

    Attributes:
        document_id: Stable identifier for the document.
        source_path: Absolute filesystem path to the document.
        source: Logical source tag (e.g., ``docs``).
        language: ISO language code for downstream tagging.
        sha256: SHA-256 hex digest of the raw document content.
        tags: Optional extra metadata fields.
    """

    document_id: str
    source_path: str
    source: str
    language: str
    sha256: str
    tags: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        """Validate DocumentRecord fields.

        Purpose:
            Ensure required metadata is present and consistent.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: If any field is missing or malformed.

        Example:
            >>> DocumentRecord(
            ...     document_id=\"doc-1\",
            ...     source_path=\"/tmp/doc.md\",
            ...     source=\"docs\",
            ...     language=\"ru\",
            ...     sha256=\"a\" * 64,
            ... )
        """
        if not self.document_id or not self.document_id.strip():
            raise ValueError("document_id cannot be empty.")
        if not self.source_path or not self.source_path.strip():
            raise ValueError("source_path cannot be empty.")
        if not self.source or not self.source.strip():
            raise ValueError("source cannot be empty.")
        if not self.language or not self.language.strip():
            raise ValueError("language cannot be empty.")
        if len(self.sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.sha256.lower()
        ):
            raise ValueError("sha256 must be a 64-character hexadecimal string.")


@dataclass(frozen=True)
class DocumentPayload:
    """Preprocessed document payload.

    Purpose:
        Bundle a document record with its cleaned textual content for chunking.

    Attributes:
        record: Canonical document metadata.
        content: Normalised plain-text content of the document.
    """

    record: DocumentRecord
    content: str

    def __post_init__(self) -> None:
        """Validate DocumentPayload fields.

        Purpose:
            Ensure the payload includes usable text content.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: When content is empty.

        Example:
            >>> DocumentPayload(
            ...     record=DocumentRecord(
            ...         document_id="doc-1",
            ...         source_path="/tmp/doc.md",
            ...         source="docs",
            ...         language="ru",
            ...         sha256="a" * 64,
            ...     ),
            ...     content="Hello world",
            ... )
        """
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty.")


@dataclass(frozen=True)
class ChunkingSettings:
    """Chunking configuration.

    Purpose:
        Capture token window parameters used during chunk generation.

    Attributes:
        chunk_size_tokens: Target number of tokens per chunk.
        chunk_overlap_tokens: Overlap tokens between adjacent chunks.
        min_chunk_tokens: Minimum number of tokens for tail chunks.
    """

    chunk_size_tokens: int
    chunk_overlap_tokens: int
    min_chunk_tokens: int = 200

    def __post_init__(self) -> None:
        """Validate chunking configuration.

        Purpose:
            Ensure chunking parameters are internally consistent.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: When the configuration is invalid.

        Example:
            >>> ChunkingSettings(chunk_size_tokens=1200, chunk_overlap_tokens=200)
            ChunkingSettings(chunk_size_tokens=1200, chunk_overlap_tokens=200, min_chunk_tokens=200)
        """
        if self.chunk_size_tokens <= 0:
            raise ValueError("chunk_size_tokens must be positive.")
        if self.chunk_overlap_tokens < 0:
            raise ValueError("chunk_overlap_tokens must be non-negative.")
        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            raise ValueError("chunk_overlap_tokens must be smaller than chunk_size_tokens.")
        if self.min_chunk_tokens <= 0:
            raise ValueError("min_chunk_tokens must be positive.")
        if self.min_chunk_tokens > self.chunk_size_tokens:
            raise ValueError("min_chunk_tokens cannot exceed chunk_size_tokens.")


@dataclass(frozen=True)
class DocumentChunk:
    """Immutable chunk representation.

    Purpose:
        Store chunked text derived from a document for embedding generation.

    Attributes:
        chunk_id: Unique chunk identifier.
        document_id: Identifier of the parent document.
        ordinal: Zero-based ordering of the chunk.
        text: Chunk payload.
        token_count: Estimated token length of the chunk.
        metadata: Optional key/value metadata for downstream indexing.
    """

    chunk_id: str
    document_id: str
    ordinal: int
    text: str
    token_count: int
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        """Validate DocumentChunk fields.

        Purpose:
            Guarantee structural integrity before persistence.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: When a field value is invalid.

        Example:
            >>> DocumentChunk(
            ...     chunk_id=\"chunk-1\",
            ...     document_id=\"doc-1\",
            ...     ordinal=0,
            ...     text=\"content\",
            ...     token_count=128,
            ... )
        """
        if not self.chunk_id or not self.chunk_id.strip():
            raise ValueError("chunk_id cannot be empty.")
        if not self.document_id or not self.document_id.strip():
            raise ValueError("document_id cannot be empty.")
        if self.ordinal < 0:
            raise ValueError("ordinal must be non-negative.")
        if not self.text or not self.text.strip():
            raise ValueError("text cannot be empty.")
        if self.token_count <= 0:
            raise ValueError("token_count must be positive.")


@dataclass(frozen=True)
class EmbeddingVector:
    """Embedding vector value object.

    Purpose:
        Encapsulate embedding payloads returned by the LLM API.

    Attributes:
        values: Tuple of embedding floats.
        model: Embedding model identifier.
        dimension: Expected length of the vector.
        metadata: Optional metadata associated with the embedding.
    """

    values: Tuple[float, ...]
    model: str
    dimension: int
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        """Validate EmbeddingVector fields.

        Purpose:
            Ensure the vector is correctly dimensioned and labelled.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: When the vector is empty or inconsistent.

        Example:
            >>> EmbeddingVector(
            ...     values=(0.1, 0.2),
            ...     model=\"text-embedding-3-small\",
            ...     dimension=2,
            ... )
        """
        if self.dimension <= 0:
            raise ValueError("dimension must be positive.")
        if len(self.values) != self.dimension:
            raise ValueError("values length must match dimension.")
        if not self.model or not self.model.strip():
            raise ValueError("model cannot be empty.")

    def as_list(self) -> list[float]:
        """Return a mutable copy of vector values.

        Purpose:
            Provide consumers with a list representation safe for mutation.

        Args:
            None.

        Returns:
            list[float]: Copy of the embedding values.

        Raises:
            ValueError: Never raised.

        Example:
            >>> vector = EmbeddingVector(
            ...     values=(0.1, 0.2),
            ...     model="text-embedding-3-small",
            ...     dimension=2,
            ... )
            >>> vector.as_list()
            [0.1, 0.2]
        """
        return list(self.values)
