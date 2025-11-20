"""Retrieval service for RAG system."""

from __future__ import annotations

import asyncio
from typing import Iterable, Sequence

from src.domain.embedding_index import EmbeddingVector
from src.domain.rag import (
    FilterConfig,
    RelevanceFilterService,
    RerankerService,
    RetrievedChunk,
    VectorSearchService,
)
from src.infrastructure.logging import get_logger


class RetrievalService:
    """Coordinate retrieval workflow (search → filter → rerank).

    Purpose:
        Encapsulate the retrieval pipeline while respecting Clean Architecture
        boundaries (domain interfaces only).
    """

    def __init__(
        self,
        vector_search: VectorSearchService,
        relevance_filter: RelevanceFilterService | None = None,
        reranker: RerankerService | None = None,
        headroom_multiplier: int = 2,
    ) -> None:
        """Initialise retrieval service with dependencies.

        Purpose:
            Capture collaborators required for the retrieval pipeline.

        Args:
            vector_search: Service for vector similarity search.
            relevance_filter: Threshold-based filter implementation.
            reranker: Advanced reranker implementation (LLM, cross-encoder).
            headroom_multiplier: Factor for pre-filter retrieval (default: 2).
        """
        self._vector_search = vector_search
        self._relevance_filter = relevance_filter
        self._reranker = reranker
        self._headroom_multiplier = headroom_multiplier
        self._logger = get_logger(__name__)

    async def retrieve(
        self,
        query_text: str,
        query_vector: EmbeddingVector,
        filter_config: FilterConfig,
    ) -> Sequence[RetrievedChunk]:
        """Retrieve, filter, and optionally rerank chunks."""
        raw_chunks = self._vector_search.search(
            query_vector=query_vector,
            top_k=filter_config.top_k * self._headroom_multiplier,
            score_threshold=0.0,
        )
        filtered = self._apply_filter(raw_chunks, filter_config)
        if not filtered:
            return []
        reranked = await self._maybe_rerank(
            query_text=query_text,
            chunks=filtered,
            filter_config=filter_config,
        )
        return list(reranked[: filter_config.top_k])

    def _apply_filter(
        self,
        chunks: Sequence[RetrievedChunk],
        filter_config: FilterConfig,
    ) -> list[RetrievedChunk]:
        if self._relevance_filter is None or filter_config.score_threshold <= 0:
            return list(chunks)[: filter_config.top_k]
        return list(
            self._relevance_filter.filter_chunks(
                chunks=chunks,
                threshold=filter_config.score_threshold,
                top_k=filter_config.top_k,
            )
        )

    async def _maybe_rerank(
        self,
        *,
        query_text: str,
        chunks: Iterable[RetrievedChunk],
        filter_config: FilterConfig,
    ) -> list[RetrievedChunk]:
        chunk_list = list(chunks)
        if not (self._reranker and filter_config.reranker_enabled and chunk_list):
            return chunk_list
        try:
            result = await self._reranker.rerank(query_text, chunk_list)
            return list(result.chunks)
        except Exception as error:  # noqa: BLE001
            self._logger.warning(
                "rag_rerank_failed",
                extra={
                    "reason": str(error),
                    "strategy": filter_config.reranker_strategy,
                },
            )
            return chunk_list


class RetrievalServiceCompat:
    """Backward-compatible adapter for legacy callers (EP20)."""

    def __init__(
        self,
        service: RetrievalService,
        default_query_text: str = "",
    ) -> None:
        """Create adapter wrapping the asynchronous retrieval service."""
        self._service = service
        self._default_query_text = default_query_text

    def retrieve(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[RetrievedChunk]:
        """Expose synchronous API matching the EP20 behaviour."""
        config = FilterConfig(score_threshold=score_threshold, top_k=top_k)
        coroutine = self._service.retrieve(
            query_text=self._default_query_text,
            query_vector=query_vector,
            filter_config=config,
        )
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)
        raise RuntimeError(
            "RetrievalServiceCompat.retrieve cannot run inside an active event loop."
        )
