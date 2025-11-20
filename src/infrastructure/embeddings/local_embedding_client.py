"""Local embedding client prototype."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import httpx

from src.domain.embedding_index.value_objects import EmbeddingVector


class EmbeddingClientError(RuntimeError):
    """Error raised when embedding generation fails.

    Purpose:
        Provide a dedicated exception type for embedding client failures.

    Args:
        message: Human-readable error message.

    Example:
        >>> raise EmbeddingClientError(\"Failed to connect\")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        EmbeddingClientError: Failed to connect
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class LocalEmbeddingClient:
    """Client for the local OpenAI-compatible embedding endpoint.

    Purpose:
        Submit text batches to the local embedding API and return domain
        embedding vectors.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 10.0,
        use_ollama_format: bool = False,
    ) -> None:
        """Initialise the client.

        Purpose:
            Store configuration required for embedding requests.

        Args:
            base_url: Base URL of the embedding service.
            model: Embedding model identifier to request.
            timeout: Request timeout in seconds.
            use_ollama_format: If True, use Ollama /api/embeddings format.

        Example:
            >>> LocalEmbeddingClient(
            ...     base_url="http://127.0.0.1:8000",
            ...     model="text-embedding-3-small",
            ... )  # doctest: +ELLIPSIS
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._use_ollama = use_ollama_format

    def generate_embeddings(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        """Generate embeddings for the provided texts.

        Purpose:
            Call the embedding endpoint and normalise the response payload.

        Args:
            texts: Sequence of plain-text inputs to embed.

        Returns:
            list[EmbeddingVector]: Embedding vectors matching the input order.

        Raises:
            ValueError: If ``texts`` is empty or contains blank items.
            EmbeddingClientError: If the HTTP request or response parsing fails.

        Example:
            >>> client = LocalEmbeddingClient(
            ...     base_url=\"http://127.0.0.1:8000\",
            ...     model=\"text-embedding-3-small\",
            ... )
            >>> # client.generate_embeddings([\"hello\"])  # doctest: +SKIP
        """
        if self._use_ollama:
            return self._generate_ollama_batch(texts)
        payload = self._build_payload(texts)
        response = self._request_embeddings(payload)
        return self._parse_response(response)

    def _generate_ollama_batch(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        """Generate embeddings using Ollama /api/embeddings (one text at a time).

        Purpose:
            Ollama embedding endpoint accepts single prompt per request.

        Args:
            texts: Sequence of texts to embed.

        Returns:
            list[EmbeddingVector]: Embedding vectors.

        Raises:
            ValueError: If texts is empty or contains blank items.
            EmbeddingClientError: If HTTP request fails.
        """
        if not texts:
            raise ValueError("texts must contain at least one item.")
        vectors = []
        url = f"{self._base_url}/api/embeddings"
        for text in texts:
            if not text or not text.strip():
                raise ValueError("text items cannot be blank.")
            payload = {"model": self._model, "prompt": text}
            try:
                response = httpx.post(url, json=payload, timeout=self._timeout)
                response.raise_for_status()
                data = response.json()
                embedding = data.get("embedding")
                if not embedding or not isinstance(embedding, list):
                    raise EmbeddingClientError(
                        "Invalid Ollama response: missing embedding."
                    )
                vectors.append(
                    EmbeddingVector(
                        values=tuple(embedding),
                        model=self._model,
                        dimension=len(embedding),
                        metadata={},
                    )
                )
            except httpx.HTTPError as error:
                raise EmbeddingClientError(f"Ollama request failed: {error}") from error
        return vectors

    def _build_payload(self, texts: Sequence[str]) -> dict[str, Any]:
        """Validate inputs and build the embedding payload.

        Purpose:
            Ensure the API receives only clean, non-empty strings.

        Args:
            texts: Sequence of texts to embed.

        Returns:
            dict[str, Any]: JSON payload for the API.

        Raises:
            ValueError: If the sequence is empty or contains blank strings.
            EmbeddingClientError: Never raised.

        Example:
            >>> client = LocalEmbeddingClient(
            ...     base_url=\"http://127.0.0.1:8000\",
            ...     model=\"text-embedding-3-small\",
            ... )
            >>> client._build_payload([\"text\"])
            {'model': 'text-embedding-3-small', 'input': ['text']}
        """
        if not texts:
            raise ValueError("texts must contain at least one item.")
        cleaned: list[str] = []
        for text in texts:
            if not text or not text.strip():
                raise ValueError("text items cannot be blank.")
            cleaned.append(text)
        return {"model": self._model, "input": cleaned}

    def _request_embeddings(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Call the embedding endpoint and return JSON data.

        Purpose:
            Execute the HTTP request and surface HTTP/JSON issues uniformly.

        Args:
            payload: Serialised request body passed to the API.

        Returns:
            dict[str, Any]: Parsed JSON payload returned by the service.

        Raises:
            EmbeddingClientError: If the HTTP call fails or JSON decoding fails.

        Example:
            >>> client = LocalEmbeddingClient(
            ...     base_url=\"http://127.0.0.1:8000\",
            ...     model=\"text-embedding-3-small\",
            ... )
            >>> # client._request_embeddings({...})  # doctest: +SKIP
        """
        url = f"{self._base_url}/v1/embeddings"
        try:
            response = httpx.post(url, json=payload, timeout=self._timeout)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise EmbeddingClientError(f"Embedding request failed: {error}") from error
        try:
            return response.json()
        except ValueError as error:
            raise EmbeddingClientError(
                "Embedding response was not valid JSON."
            ) from error

    def _parse_response(self, data: dict[str, Any]) -> list[EmbeddingVector]:
        """Transform the JSON payload into embedding vectors.

        Purpose:
            Validate the response schema and convert entries to value objects.

        Args:
            data: JSON payload returned by the embedding endpoint.

        Returns:
            list[EmbeddingVector]: Vector objects ready for persistence.

        Raises:
            EmbeddingClientError: If the payload structure is invalid.

        Example:
            >>> client = LocalEmbeddingClient(
            ...     base_url="http://127.0.0.1:8000",
            ...     model="text-embedding-3-small",
            ... )
            >>> client._parse_response({
            ...     "model": "text-embedding-3-small",
            ...     "data": [{"embedding": [0.1]}],
            ... })  # doctest: +ELLIPSIS
        """
        if "data" not in data or not isinstance(data["data"], Iterable):
            raise EmbeddingClientError("Embedding response missing 'data' array.")
        vectors: list[EmbeddingVector] = []
        model = str(data.get("model", self._model))
        for item in data["data"]:
            vector = self._parse_item(item=item, model=model)
            vectors.append(vector)
        if not vectors:
            raise EmbeddingClientError("Embedding response contained no vectors.")
        return vectors

    def _parse_item(self, item: Any, model: str) -> EmbeddingVector:
        """Transform a single embedding entry into a value object.

        Purpose:
            Convert a raw embedding payload into an EmbeddingVector.

        Args:
            item: Raw JSON dictionary describing a single embedding.
            model: Model identifier associated with the embedding.

        Returns:
            EmbeddingVector: Parsed embedding descriptor.

        Raises:
            EmbeddingClientError: If the item is malformed.

        Example:
            >>> client = LocalEmbeddingClient(
            ...     base_url="http://127.0.0.1:8000",
            ...     model="text-embedding-3-small",
            ... )
            >>> client._parse_item({"embedding": [0.1]}, model="text-embedding-3-small")  # doctest: +ELLIPSIS
        """
        if not isinstance(item, dict) or "embedding" not in item:
            raise EmbeddingClientError("Embedding item missing 'embedding' field.")
        raw_values = item["embedding"]
        if not isinstance(raw_values, Iterable):
            raise EmbeddingClientError("Embedding vector must be iterable.")
        values = tuple(float(value) for value in raw_values)
        if not values:
            raise EmbeddingClientError("Embedding vector must not be empty.")
        return EmbeddingVector(values=values, model=model, dimension=len(values))
