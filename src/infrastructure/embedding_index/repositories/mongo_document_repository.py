"""MongoDB repositories for embedding index metadata."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable, Sequence

from pymongo.collection import Collection
from pymongo.operations import UpdateOne

from src.domain.embedding_index import (
    ChunkRepository,
    DocumentChunk,
    DocumentRecord,
    DocumentRepository,
)


def _deserialize_chunk(payload: dict) -> DocumentChunk:
    metadata = payload.get("metadata") or {}
    return DocumentChunk(
        chunk_id=payload["chunk_id"],
        document_id=payload["document_id"],
        ordinal=int(payload.get("ordinal", 0)),
        text=payload.get("text", ""),
        token_count=int(payload.get("token_count", 0)),
        metadata={str(key): str(value) for key, value in metadata.items()},
    )


class MongoDocumentRepository(DocumentRepository):
    """Persist document metadata into MongoDB."""

    def __init__(self, collection: Collection, *, ensure_indexes: bool = True) -> None:
        """Initialise repository."""
        self._collection = collection
        if ensure_indexes:
            self._collection.create_index("document_id", unique=True)

    def upsert_document(self, record: DocumentRecord) -> None:
        """Insert or update document metadata."""
        payload = asdict(record)
        self._collection.update_one(
            {"document_id": record.document_id},
            {"$set": payload},
            upsert=True,
        )

    def get_document_by_id(self, document_id: str) -> DocumentRecord | None:
        """Return document metadata by identifier."""
        payload = self._collection.find_one({"document_id": document_id})
        if not payload:
            return None
        tags = payload.get("tags") or {}
        return DocumentRecord(
            document_id=payload["document_id"],
            source_path=payload.get("source_path", ""),
            source=payload.get("source", ""),
            language=payload.get("language", ""),
            sha256=payload.get("sha256", ""),
            tags={str(key): str(value) for key, value in tags.items()},
        )


class MongoChunkRepository(ChunkRepository):
    """Persist document chunks into MongoDB."""

    def __init__(self, collection: Collection, *, ensure_indexes: bool = True) -> None:
        """Initialise repository."""
        self._collection = collection
        if ensure_indexes:
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

    def get_chunks_by_ids(self, chunk_ids: Sequence[str]) -> Sequence[DocumentChunk]:
        """Fetch chunks by their identifiers preserving input order."""
        if not chunk_ids:
            return []
        cursor = self._collection.find({"chunk_id": {"$in": list(chunk_ids)}})
        chunk_map = {doc["chunk_id"]: _deserialize_chunk(doc) for doc in cursor}
        return [chunk_map[cid] for cid in chunk_ids if cid in chunk_map]
