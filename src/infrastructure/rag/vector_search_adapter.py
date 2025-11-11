"""Vector search adapter for RAG system."""

from __future__ import annotations

import math
import pickle
from pathlib import Path
from typing import Dict, Sequence, Tuple

from src.domain.embedding_index import (
    ChunkRepository,
    DocumentRepository,
    EmbeddingVector,
)
from src.domain.rag import RetrievedChunk
from src.infrastructure.logging import get_logger


class VectorSearchAdapter:
    """Adapter for vector similarity search (implements VectorSearchService protocol).

    Purpose:
        Perform KNN search against the persisted embedding store (FAISS fallback)
        and fetch chunk metadata from MongoDB.
    """

    def __init__(
        self,
        *,
        chunk_repository: ChunkRepository,
        document_repository: DocumentRepository | None = None,
        fallback_index_path: Path | None = None,
    ) -> None:
        """Initialise vector search adapter with dependencies.

        Args:
            chunk_repository: Repository for chunk metadata.
            document_repository: Repository for document metadata (optional but
                recommended for populating source paths).
            fallback_index_path: Path to pickle file produced by indexer when
                Redis is unavailable. Defaults to `var/indices/embedding_index_v1.pkl`.
        """
        self._chunk_repository = chunk_repository
        self._document_repository = document_repository
        self._logger = get_logger(__name__)
        self._fallback_index_path = fallback_index_path or Path(
            "var/indices/embedding_index_v1.pkl"
        )
        self._fallback_vectors: Dict[str, EmbeddingVector] | None = None
        self._document_cache: Dict[str, str] = {}

    def search(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[RetrievedChunk]:
        """Return top-k chunks above similarity threshold."""

        candidates = self._search_fallback(query_vector, top_k, score_threshold)
        if not candidates:
            return []

        chunk_ids = [chunk_id for chunk_id, _ in candidates]
        chunks = self._chunk_repository.get_chunks_by_ids(chunk_ids)
        chunk_map = {chunk.chunk_id: chunk for chunk in chunks}

        results: list[RetrievedChunk] = []
        for chunk_id, score in candidates:
            chunk = chunk_map.get(chunk_id)
            if not chunk:
                continue
            metadata_dict = {
                str(key): str(value) for key, value in (chunk.metadata or {}).items()
            }
            source_path = (
                metadata_dict.get("source_path")
                or metadata_dict.get("path")
                or self._resolve_document_path(chunk.document_id)
                or "unknown"
            )
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    similarity_score=score,
                    source_path=source_path,
                    metadata=metadata_dict,
                )
            )
        return results

    def _search_fallback(
        self,
        query_vector: EmbeddingVector,
        top_k: int,
        score_threshold: float,
    ) -> Sequence[Tuple[str, float]]:
        vectors = self._load_fallback_vectors()
        if not vectors:
            self._logger.warning(
                "vector_search_fallback_missing",
                message="Fallback embedding index not found; returning empty results",
                path=str(self._fallback_index_path),
            )
            return []

        query_values = list(query_vector.values)
        query_norm = self._vector_norm(query_values)
        if query_norm == 0:
            self._logger.warning("vector_search_zero_query_norm")
            return []

        similarities: list[Tuple[str, float]] = []
        for chunk_id, embedding in vectors.items():
            if embedding.dimension != query_vector.dimension:
                continue
            values = list(embedding.values)
            score = self._cosine_similarity(query_values, values, query_norm)
            if score >= score_threshold:
                similarities.append((chunk_id, score))

        similarities.sort(key=lambda item: item[1], reverse=True)
        return similarities[:top_k]

    def _load_fallback_vectors(self) -> Dict[str, EmbeddingVector] | None:
        if self._fallback_vectors is not None:
            return self._fallback_vectors
        if not self._fallback_index_path.exists():
            return None
        try:
            with self._fallback_index_path.open("rb") as handle:
                self._fallback_vectors = pickle.load(handle)
        except (OSError, pickle.PickleError) as error:
            self._logger.error(
                "vector_search_fallback_load_failed",
                error=str(error),
                path=str(self._fallback_index_path),
            )
            self._fallback_vectors = None
        return self._fallback_vectors

    def _resolve_document_path(self, document_id: str) -> str | None:
        if document_id in self._document_cache:
            return self._document_cache[document_id]
        if not self._document_repository:
            return None
        record = self._document_repository.get_document_by_id(document_id)
        if not record:
            return None
        self._document_cache[document_id] = record.source_path
        return record.source_path

    @staticmethod
    def _cosine_similarity(
        query: Sequence[float],
        candidate: Sequence[float],
        query_norm: float,
    ) -> float:
        candidate_norm = VectorSearchAdapter._vector_norm(candidate)
        if candidate_norm == 0:
            return 0.0
        dot = sum(q * c for q, c in zip(query, candidate))
        return dot / (query_norm * candidate_norm)

    @staticmethod
    def _vector_norm(values: Sequence[float]) -> float:
        return math.sqrt(sum(value * value for value in values))
