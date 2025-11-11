"""Unit tests for LocalEmbeddingClient prototype."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.infrastructure.embeddings.local_embedding_client import (
    EmbeddingClientError,
    LocalEmbeddingClient,
)


@pytest.fixture(name="client")
def fixture_client() -> LocalEmbeddingClient:
    """Create LocalEmbeddingClient instance for tests."""
    return LocalEmbeddingClient(
        base_url="http://127.0.0.1:8000",
        model="text-embedding-3-small",
        timeout=5.0,
    )


def _mock_response(payload: dict[str, Any]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_generate_embeddings_returns_vectors(client: LocalEmbeddingClient) -> None:
    """Ensure the client transforms HTTP payloads into domain vectors."""
    payload = {
        "data": [
            {"embedding": [0.1, 0.2, 0.3], "index": 0},
            {"embedding": [0.4, 0.5, 0.6], "index": 1},
        ],
        "model": "text-embedding-3-small",
    }

    with patch("src.infrastructure.embeddings.local_embedding_client.httpx.post") as mock_post:
        mock_post.return_value = _mock_response(payload)
        vectors = client.generate_embeddings(["one", "two"])

    assert len(vectors) == 2
    assert vectors[0].dimension == 3
    assert vectors[0].model == "text-embedding-3-small"


def test_generate_embeddings_requires_input(client: LocalEmbeddingClient) -> None:
    """Ensure empty payloads raise ValueError."""
    with pytest.raises(ValueError):
        client.generate_embeddings([])


def test_generate_embeddings_raises_on_http_error(client: LocalEmbeddingClient) -> None:
    """Ensure HTTP errors surface as EmbeddingClientError."""
    http_error = httpx.HTTPStatusError(
        message="error",
        request=MagicMock(),
        response=MagicMock(status_code=500),
    )

    with patch("src.infrastructure.embeddings.local_embedding_client.httpx.post") as mock_post:
        response = MagicMock()
        response.raise_for_status.side_effect = http_error
        mock_post.return_value = response

        with pytest.raises(EmbeddingClientError):
            client.generate_embeddings(["text"])


def test_generate_embeddings_validates_response_shape(client: LocalEmbeddingClient) -> None:
    """Ensure missing embedding data triggers EmbeddingClientError."""
    payload = {"model": "text-embedding-3-small", "data": []}

    with patch("src.infrastructure.embeddings.local_embedding_client.httpx.post") as mock_post:
        mock_post.return_value = _mock_response(payload)

        with pytest.raises(EmbeddingClientError):
            client.generate_embeddings(["text"])

