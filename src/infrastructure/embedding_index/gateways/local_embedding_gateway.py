"""Embedding gateway wrapping the local embedding client."""

from __future__ import annotations

import hashlib
from typing import Sequence

from src.domain.embedding_index import DocumentChunk, EmbeddingGateway, EmbeddingVector
from src.infrastructure.embeddings.local_embedding_client import (
    EmbeddingClientError,
    LocalEmbeddingClient,
)
from src.infrastructure.logging import get_logger


class LocalEmbeddingGateway(EmbeddingGateway):
    """Bridge between application layer and LocalEmbeddingClient.

    Purpose:
        Convert ``DocumentChunk`` instances into embedding vectors using the
        local OpenAI-compatible API with deterministic fallback support.
    """

    def __init__(self, client: LocalEmbeddingClient, fallback_dimension: int) -> None:
        """Initialise gateway with the underlying client."""
        self._client = client
        self._fallback_dimension = fallback_dimension
        self._logger = get_logger(__name__)

    def embed(self, chunks: Sequence[DocumentChunk]) -> Sequence[EmbeddingVector]:
        """Generate embeddings for given document chunks."""
        texts = [chunk.text for chunk in chunks]
        try:
            return self._client.generate_embeddings(texts)
        except EmbeddingClientError as error:
            self._logger.warning(
                "embedding_api_unavailable",
                error=str(error),
                fallback="sha256",
            )
            return [self._fallback_vector(chunk) for chunk in chunks]

    def _fallback_vector(self, chunk: DocumentChunk) -> EmbeddingVector:
        """Generate deterministic fallback embedding using SHA-256."""
        values = []
        counter = 0
        seed = chunk.text.encode("utf-8")
        while len(values) < self._fallback_dimension:
            payload = seed + counter.to_bytes(4, "little")
            digest = hashlib.sha256(payload).digest()
            values.extend(byte / 255.0 for byte in digest)
            counter += 1
        trimmed = tuple(values[: self._fallback_dimension])
        return EmbeddingVector(
            values=trimmed,
            model="fallback-sha256",
            dimension=self._fallback_dimension,
            metadata={"fallback": "sha256"},
        )

