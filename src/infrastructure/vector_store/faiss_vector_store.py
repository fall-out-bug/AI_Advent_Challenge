"""Local FAISS-compatible vector store fallback."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, Sequence

from src.domain.embedding_index import DocumentChunk, EmbeddingVector, VectorStore
from src.infrastructure.logging import get_logger


class FaissVectorStore(VectorStore):
    """Persist embeddings to local storage when Redis RediSearch is unavailable.

    Purpose:
        Provide a simple file-backed fallback that can later be upgraded to a
        true FAISS index without changing the application contract.
    """

    def __init__(self, index_path: Path, dimension: int) -> None:
        self._index_path = index_path
        self._dimension = dimension
        self._logger = get_logger(__name__)
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._vectors: Dict[str, EmbeddingVector] = {}
        self._load()

    def upsert(
        self,
        chunks: Sequence[DocumentChunk],
        vectors: Sequence[EmbeddingVector],
    ) -> None:
        """Persist embeddings to disk."""
        for chunk, vector in zip(chunks, vectors):
            if vector.dimension != self._dimension:
                self._logger.warning(
                    "faiss_fallback_dimension_mismatch",
                    chunk_id=chunk.chunk_id,
                    expected=self._dimension,
                    actual=vector.dimension,
                )
            self._vectors[chunk.chunk_id] = vector
        self._persist()

    def _load(self) -> None:
        if not self._index_path.exists():
            return
        try:
            with self._index_path.open("rb") as handle:
                self._vectors = pickle.load(handle)
        except (OSError, pickle.PickleError) as error:
            self._logger.warning(
                "faiss_fallback_load_failed",
                path=str(self._index_path),
                error=str(error),
            )
            self._vectors = {}

    def _persist(self) -> None:
        try:
            with self._index_path.open("wb") as handle:
                pickle.dump(self._vectors, handle)
        except (OSError, pickle.PickleError) as error:
            self._logger.error(
                "faiss_fallback_persist_failed",
                path=str(self._index_path),
                error=str(error),
            )
