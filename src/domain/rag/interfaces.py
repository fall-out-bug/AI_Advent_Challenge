"""RAG domain interfaces (protocols)."""

from __future__ import annotations

from typing import Protocol, Sequence

from src.domain.embedding_index import EmbeddingVector

from .value_objects import Answer, RetrievedChunk, RerankResult


class VectorSearchService(Protocol):
    """Search for similar vectors in the embedding index.

    Purpose:
        Abstract vector similarity search across different backends
        (Redis, FAISS, etc.) while staying in the domain layer.
    """

    def search(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[RetrievedChunk]:
        """Return top-k chunks above similarity threshold.

        Purpose:
            Perform KNN search and return ranked chunks with metadata.

        Args:
            query_vector: Query embedding vector.
            top_k: Maximum number of results to return.
            score_threshold: Minimum similarity score (0.0-1.0).

        Returns:
            Sequence of retrieved chunks, ordered by descending similarity.

        Raises:
            RuntimeError: If vector store is unavailable.

        Example:
            >>> service = ...  # doctest: +SKIP
            >>> query_vec = EmbeddingVector(values=(0.1, 0.2), model="...", dimension=2)
            >>> chunks = service.search(query_vec, top_k=5, score_threshold=0.3)
        """


class LLMService(Protocol):
    """Generate text completions from prompts.

    Purpose:
        Abstract LLM API calls while staying in the domain layer.
    """

    def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Answer:
        """Generate completion and return answer with metadata.

        Purpose:
            Call LLM API with prompt and return structured answer.

        Args:
            prompt: Formatted prompt string.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            Answer value object with text and metadata.

        Raises:
            RuntimeError: If LLM API is unavailable.

        Example:
            >>> service = ...  # doctest: +SKIP
            >>> answer = service.generate(
            ...     "Вопрос: ...",
            ...     max_tokens=1000,
            ...     temperature=0.7,
            ... )
        """


class RelevanceFilterService(Protocol):
    """Filter chunks by relevance threshold.

    Purpose:
        Provide a domain-level contract for threshold-based filtering without
        imposing implementation details.
    """

    def filter_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
        threshold: float,
        top_k: int,
    ) -> Sequence[RetrievedChunk]:
        """Return chunks above threshold, limited to top_k."""


class RerankerService(Protocol):
    """Rerank chunks using advanced scoring."""

    async def rerank(
        self,
        query: str,
        chunks: Sequence[RetrievedChunk],
    ) -> RerankResult:
        """Rescore and reorder chunks by relevance."""
