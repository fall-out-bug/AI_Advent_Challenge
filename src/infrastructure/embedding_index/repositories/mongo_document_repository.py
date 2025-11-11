"""MongoDB repositories for embedding index metadata."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from pymongo.collection import Collection
from pymongo.operations import UpdateOne

from src.domain.embedding_index import (
    ChunkRepository,
    DocumentChunk,
    DocumentRecord,
    DocumentRepository,
)


class MongoDocumentRepository(DocumentRepository):
    """Persist document metadata into MongoDB."""

    def __init__(self, collection: Collection) -> None:
        """Initialise repository."""
        self._collection = collection
        self._collection.create_index("document_id", unique=True)

    def upsert_document(self, record: DocumentRecord) -> None:
        """Insert or update document metadata."""
        payload = asdict(record)
        self._collection.update_one(
            {"document_id": record.document_id},
            {"$set": payload},
            upsert=True,
        )


class MongoChunkRepository(ChunkRepository):
    """Persist document chunks into MongoDB."""

    def __init__(self, collection: Collection) -> None:
        """Initialise repository."""
        self._collection = collection
        self._collection.create_index("chunk_id", unique=True)
        self._collection.create_index("document_id")

    def upsert_chunks(self, chunks: Iterable[DocumentChunk]) -> None:
        """Insert or update a batch of chunks."""
        operations = []
        for chunk in chunks:
            payload = asdict(chunk)
            operations.append(
                UpdateOne(
                    {"chunk_id": chunk.chunk_id},
                    {"$set": payload},
                    upsert=True,
                )
            )
        if operations:
            self._collection.bulk_write(operations, ordered=False)
