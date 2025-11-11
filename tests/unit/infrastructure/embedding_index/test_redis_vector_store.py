"""Tests for RedisVectorStore."""

from __future__ import annotations

from array import array
from pathlib import Path
from typing import Any, List, Tuple

from src.domain.embedding_index import DocumentChunk, EmbeddingVector
from src.infrastructure.vector_store.redis_schema_manager import RedisSchemaError
from src.infrastructure.vector_store.redis_vector_store import RedisVectorStore


class FakeRedis:
    """Fake Redis client capturing pipeline commands."""

    def __init__(self) -> None:
        self.commands: List[Tuple[str, dict[str, Any]]] = []

    def pipeline(self):
        return FakePipeline(self.commands)

    def execute_command(self, *args: Any) -> str:
        return "OK"


class FakePipeline:
    """Fake Redis pipeline."""

    def __init__(self, commands: List[Tuple[str, dict[str, Any]]]) -> None:
        self._commands = commands

    def hset(self, name: str, mapping: dict[str, Any]) -> "FakePipeline":
        self._commands.append((name, mapping))
        return self

    def execute(self) -> None:
        return None


class StubSchemaManager:
    """Schema manager stub no-op implementation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        """Initialise stub."""

    def ensure_schema(self, connection: Any) -> None:  # noqa: D401
        """No-op ensure schema."""
        return None


def _build_chunk() -> DocumentChunk:
    return DocumentChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        ordinal=0,
        text="hello",
        token_count=1,
        metadata={"stage": "19"},
    )


def _build_vector() -> EmbeddingVector:
    return EmbeddingVector(
        values=(0.1, 0.2),
        model="model",
        dimension=2,
    )


def test_vector_store_encodes_vectors() -> None:
    """Ensure vector store writes embeddings to Redis."""
    redis_client = FakeRedis()
    store = RedisVectorStore(client=redis_client, schema_manager=StubSchemaManager(), key_prefix="embedding:chunk:")  # type: ignore[arg-type]

    store.upsert([_build_chunk()], [_build_vector()])

    assert len(redis_client.commands) == 1
    name, mapping = redis_client.commands[0]
    assert name == "embedding:chunk:chunk-1"
    assert mapping["model"] == "model"
    encoded = mapping["embedding"]
    assert encoded == array("f", [0.1, 0.2]).tobytes()


def test_vector_store_uses_fallback_when_schema_unavailable(tmp_path: Path) -> None:
    """Ensure fallback store persists embeddings when RediSearch is unavailable."""

    class FailingSchemaManager:
        def ensure_schema(self, connection: Any) -> None:
            raise RedisSchemaError("missing module")

    redis_client = FakeRedis()
    store = RedisVectorStore(
        client=redis_client,
        schema_manager=FailingSchemaManager(),  # type: ignore[arg-type]
        key_prefix="embedding:chunk:",
        fallback_index_path=tmp_path / "embedding_index.pkl",
        dimension=2,
    )

    store.upsert([_build_chunk()], [_build_vector()])

    assert redis_client.commands == []
    fallback_path = tmp_path / "embedding_index.pkl"
    assert fallback_path.exists()

