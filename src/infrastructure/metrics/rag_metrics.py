"""Prometheus metrics for RAG++ pipeline."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

rag_rerank_duration_seconds = Histogram(
    "rag_rerank_duration_seconds",
    "Time spent reranking chunks.",
    ["strategy"],
    buckets=(0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0),
)

rag_chunks_filtered_total = Counter(
    "rag_chunks_filtered_total",
    "Number of chunks filtered out by threshold or top_k.",
    ["category"],
)

rag_rerank_score_delta = Histogram(
    "rag_rerank_score_delta",
    "Change in top chunk score after reranking.",
    buckets=(-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0),
)

rag_reranker_fallback_total = Counter(
    "rag_reranker_fallback_total",
    "Number of times reranker fell back to original ordering.",
    ["reason"],
)

rag_rerank_score_variance = Histogram(
    "rag_rerank_score_variance",
    "Observed variance of rerank scores across chunks.",
    buckets=(0.0, 0.05, 0.1, 0.2, 0.5, 1.0),
)

__all__ = [
    "rag_chunks_filtered_total",
    "rag_rerank_duration_seconds",
    "rag_rerank_score_delta",
    "rag_rerank_score_variance",
    "rag_reranker_fallback_total",
]
