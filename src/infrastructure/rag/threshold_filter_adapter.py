"""Threshold-based filter implementation for retrieved chunks."""

from __future__ import annotations

from typing import Sequence

from src.domain.rag import RetrievedChunk
from src.infrastructure.metrics import rag_metrics


class ThresholdFilterAdapter:
    """Filter retrieved chunks using similarity threshold."""

    def filter_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
        threshold: float,
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Return chunks with score ≥ threshold, limited to top_k."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be between 0.0 and 1.0, got {threshold}.")
        if top_k < 1:
            raise ValueError(f"top_k must be at least 1, got {top_k}.")

        below_threshold_count = 0
        passed: list[RetrievedChunk] = []
        for chunk in chunks:
            if chunk.similarity_score >= threshold:
                passed.append(chunk)
            else:
                below_threshold_count += 1

        if below_threshold_count:
            rag_metrics.rag_chunks_filtered_total.labels(
                category="below_threshold"
            ).inc(below_threshold_count)

        if len(passed) > top_k:
            rag_metrics.rag_chunks_filtered_total.labels(category="above_top_k").inc(
                len(passed) - top_k
            )

        return passed[:top_k]
