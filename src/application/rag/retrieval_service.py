"""Retrieval service for RAG system."""

from __future__ import annotations

from typing import Sequence

from src.domain.embedding_index import EmbeddingVector
from src.domain.rag import RetrievedChunk, VectorSearchService


class RetrievalService:
    """Coordinate retrieval workflow (search + fetch + rank).

    Purpose:
        Encapsulate retrieval logic while staying in the application layer.
    """

    def __init__(
        self,
        vector_search: VectorSearchService,
    ) -> None:
        """Initialise retrieval service with dependencies.

        Purpose:
            Capture injected collaborators for later execution.

        Args:
            vector_search: Service for vector similarity search.

        Example:
            >>> service = RetrievalService(vector_search=...)  # doctest: +SKIP
        """
        self._vector_search = vector_search

    def retrieve(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[RetrievedChunk]:
        """Retrieve chunks above similarity threshold.

        Purpose:
            Perform vector search and return ranked chunks with metadata.

        Args:
            query_vector: Query embedding vector.
            top_k: Maximum number of results to return.
            score_threshold: Minimum similarity score (0.0-1.0).

        Returns:
            Sequence of retrieved chunks, ordered by descending similarity.

        Raises:
            RuntimeError: If vector store is unavailable.

        Example:
            >>> service = RetrievalService(vector_search=...)  # doctest: +SKIP
            >>> query_vec = EmbeddingVector(
            ...     values=(0.1, 0.2),
            ...     model="all-MiniLM-L6-v2",
            ...     dimension=2,
            ... )
            >>> chunks = service.retrieve(query_vec, top_k=5, score_threshold=0.3)
        """
        chunks = self._vector_search.search(
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        return chunks
