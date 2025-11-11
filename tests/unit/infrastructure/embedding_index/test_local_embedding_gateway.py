"""Tests for LocalEmbeddingGateway."""

from __future__ import annotations

from typing import List
from unittest.mock import MagicMock

from src.domain.embedding_index import DocumentChunk
from src.infrastructure.embedding_index.gateways.local_embedding_gateway import (
    LocalEmbeddingGateway,
)
from src.infrastructure.embeddings.local_embedding_client import LocalEmbeddingClient


def test_gateway_delegates_to_client() -> None:
    """Ensure gateway delegates embedding generation to the client."""
    client = MagicMock(spec=LocalEmbeddingClient)
    gateway = LocalEmbeddingGateway(client=client, fallback_dimension=4)
    chunk = DocumentChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        ordinal=0,
        text="hello",
        token_count=1,
    )

    gateway.embed([chunk])

    client.generate_embeddings.assert_called_once_with(["hello"])
