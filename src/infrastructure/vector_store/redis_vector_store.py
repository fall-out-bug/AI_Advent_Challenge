"""Redis-backed vector store for embedding index."""

from __future__ import annotations

from array import array
from pathlib import Path
from typing import Mapping, Sequence

from redis import Redis

from src.domain.embedding_index import DocumentChunk, EmbeddingVector, VectorStore
from src.infrastructure.logging import get_logger
from src.infrastructure.vector_store.faiss_vector_store import FaissVectorStore
from src.infrastructure.vector_store.redis_schema_manager import (
    RedisSchemaError,
    RedisSchemaManager,
)


class RedisVectorStore(VectorStore):
    """Persist embeddings into Redis using RediSearch."""

    def __init__(
        self,
        client: Redis,
        schema_manager: RedisSchemaManager,
        *,
        key_prefix: str,
        fallback_index_path: Path | None = None,
        dimension: int | None = None,
    ) -> None:
        """Initialise vector store and ensure schema exists."""
        self._client = client
        self._key_prefix = key_prefix
        self._logger = get_logger(__name__)
        self._schema_ready = self._ensure_schema(schema_manager)
        self._fallback_store: FaissVectorStore | None = None
        if not self._schema_ready:
            index_path = fallback_index_path or Path(
                "var/indices/embedding_index_v1.pkl"
            )
            dimension = dimension or 384
            self._fallback_store = FaissVectorStore(
                index_path=index_path,
                dimension=dimension,
            )

    def upsert(
        self,
        chunks: Sequence[DocumentChunk],
        vectors: Sequence[EmbeddingVector],
    ) -> None:
        """Persist embeddings and metadata."""
        if self._schema_ready:
            pipeline = self._client.pipeline()
            for chunk, vector in zip(chunks, vectors):
                key = f"{self._key_prefix}{chunk.chunk_id}"
                mapping = self._build_mapping(chunk, vector)
                pipeline.hset(name=key, mapping=mapping)
            try:
                pipeline.execute()
            except Exception as error:  # noqa: BLE001
                self._logger.error("redis_upsert_failed", error=str(error))
                raise
        if self._fallback_store:
            self._fallback_store.upsert(chunks, vectors)

    def _build_mapping(
        self,
        chunk: DocumentChunk,
        vector: EmbeddingVector,
    ) -> Mapping[str, bytes | str]:
        """Build Redis hash mapping for a chunk."""
        payload: dict[str, bytes | str] = {
            "embedding": self._encode_vector(vector),
            "model": vector.model,
            "document_id": chunk.document_id,
        }
        for key, value in (chunk.metadata or {}).items():
            payload[key] = str(value)
        return payload

    def _encode_vector(self, vector: EmbeddingVector) -> bytes:
        """Encode embedding vector as float32 bytes."""
        return array("f", vector.values).tobytes()

    def _ensure_schema(self, schema_manager: RedisSchemaManager) -> bool:
        """Ensure RediSearch schema exists, logging on failure."""
        try:
            schema_manager.ensure_schema(connection=self._client)
            return True
        except RedisSchemaError as error:
            self._logger.warning("redis_schema_unavailable", error=str(error))
            return False
