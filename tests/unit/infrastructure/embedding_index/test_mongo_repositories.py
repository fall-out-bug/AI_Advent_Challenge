"""Tests for Mongo embedding repositories."""

from __future__ import annotations

from unittest.mock import MagicMock

from pymongo.operations import UpdateOne

from src.domain.embedding_index import DocumentChunk, DocumentRecord
from src.infrastructure.embedding_index.repositories.mongo_document_repository import (
    MongoChunkRepository,
    MongoDocumentRepository,
)


def _build_record() -> DocumentRecord:
    return DocumentRecord(
        document_id="doc-1",
        source_path="/tmp/doc.md",
        source="docs",
        language="ru",
        sha256="a" * 64,
        tags={"stage": "19"},
    )


def _build_chunk() -> DocumentChunk:
    return DocumentChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        ordinal=0,
        text="hello",
        token_count=1,
        metadata={"stage": "19"},
    )


def test_document_repository_upsert_calls_update_one() -> None:
    """Ensure document repository performs upsert."""
    collection = MagicMock()
    repo = MongoDocumentRepository(collection=collection)

    repo.upsert_document(_build_record())

    collection.update_one.assert_called_once()


def test_chunk_repository_bulk_write_called() -> None:
    """Ensure chunk repository performs bulk write."""
    collection = MagicMock()
    repo = MongoChunkRepository(collection=collection)

    repo.upsert_chunks([_build_chunk(), _build_chunk()])

    collection.bulk_write.assert_called_once()
    operations = collection.bulk_write.call_args[0][0]
    assert all(isinstance(op, UpdateOne) for op in operations)

