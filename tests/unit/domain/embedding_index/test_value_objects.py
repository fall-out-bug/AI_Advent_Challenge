"""Unit tests for embedding index domain value objects."""

from __future__ import annotations

import pytest

from src.domain.embedding_index.value_objects import (
    ChunkingSettings,
    DocumentChunk,
    DocumentPayload,
    DocumentRecord,
    EmbeddingVector,
)


def test_document_record_requires_document_id() -> None:
    """Ensure DocumentRecord rejects empty identifiers."""
    with pytest.raises(ValueError):
        DocumentRecord(
            document_id="",
            source_path="/tmp/doc.md",
            source="docs",
            language="ru",
            sha256="a" * 64,
        )


def test_document_record_requires_valid_sha256() -> None:
    """Ensure DocumentRecord validates SHA-256 length."""
    with pytest.raises(ValueError):
        DocumentRecord(
            document_id="doc-1",
            source_path="/tmp/doc.md",
            source="docs",
            language="ru",
            sha256="1234",
        )


def test_document_chunk_requires_text() -> None:
    """Ensure DocumentChunk rejects blank text payloads."""
    with pytest.raises(ValueError):
        DocumentChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            ordinal=0,
            text="   ",
            token_count=10,
        )


def test_document_chunk_requires_non_negative_ordinal() -> None:
    """Ensure DocumentChunk ordinal must be non-negative."""
    with pytest.raises(ValueError):
        DocumentChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            ordinal=-1,
            text="content",
            token_count=10,
        )


def test_embedding_vector_dimension_validation() -> None:
    """Ensure EmbeddingVector enforces dimensionality."""
    with pytest.raises(ValueError):
        EmbeddingVector(
            values=(0.1, 0.2),
            model="text-embedding-3-small",
            dimension=3,
        )


def test_embedding_vector_as_list_returns_copy() -> None:
    """Ensure EmbeddingVector exposes a list copy."""
    vector = EmbeddingVector(
        values=(0.1, 0.2, 0.3),
        model="text-embedding-3-small",
        dimension=3,
    )

    values = vector.as_list()
    values.append(0.4)

    assert vector.values == (0.1, 0.2, 0.3)


def test_document_payload_requires_non_empty_content() -> None:
    """Ensure DocumentPayload validates content."""
    with pytest.raises(ValueError):
        DocumentPayload(
            record=DocumentRecord(
                document_id="doc-1",
                source_path="/tmp/doc.md",
                source="docs",
                language="ru",
                sha256="a" * 64,
            ),
            content="",
        )


def test_chunking_settings_validate_values() -> None:
    """Ensure ChunkingSettings enforces positive configuration."""
    with pytest.raises(ValueError):
        ChunkingSettings(chunk_size_tokens=0, chunk_overlap_tokens=0)
