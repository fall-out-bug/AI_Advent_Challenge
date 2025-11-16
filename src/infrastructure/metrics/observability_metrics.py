"""Shared observability metrics used across Epic 23 instrumentation."""

from __future__ import annotations

from typing import Optional

try:
    from prometheus_client import Gauge, Histogram, Counter, REGISTRY

    _registry = REGISTRY

    benchmark_export_duration_seconds = Histogram(
        "benchmark_export_duration_seconds",
        "Time spent exporting benchmark datasets.",
        ("exporter",),
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
        registry=_registry,
    )

    shared_infra_bootstrap_status = Gauge(
        "shared_infra_bootstrap_status",
        "Status of shared infrastructure bootstrap steps (0 = failure, 1 = success).",
        ("step",),
        registry=_registry,
    )

    structured_logs_total = Counter(
        "structured_logs_total",
        "Number of structured log entries emitted.",
        ("service", "level"),
        registry=_registry,
    )

    rag_variance_ratio = Gauge(
        "rag_variance_ratio",
        "Observed variance ratio for RAG reranker evaluations (owner-only).",
        ("window",),
        registry=_registry,
    )
    rag_fallback_reason_total = Counter(
        "rag_fallback_reason_total",
        "Number of times RAG reranker fell back to original ordering (owner-only).",
        ("reason",),
        registry=_registry,
    )
except ImportError:  # pragma: no cover - metrics optional for local runs

    class _DummyMetric:
        def labels(self, *args, **kwargs):  # type: ignore[override]
            return self

        def observe(self, *args, **kwargs):  # type ignore
            return None

        def inc(self, *args, **kwargs):  # type: ignore[override]
            return None

        def set(self, *args, **kwargs):  # type: ignore[override]
            return None

    benchmark_export_duration_seconds = _DummyMetric()
    shared_infra_bootstrap_status = _DummyMetric()
    structured_logs_total = _DummyMetric()
    rag_variance_ratio = _DummyMetric()
    rag_fallback_reason_total = _DummyMetric()


__all__ = [
    "benchmark_export_duration_seconds",
    "shared_infra_bootstrap_status",
    "structured_logs_total",
    "rag_variance_ratio",
    "rag_fallback_reason_total",
]
