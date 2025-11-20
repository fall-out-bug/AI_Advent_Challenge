"""Prometheus metrics for voice agent functionality.

Purpose:
    Defines voice transcription metrics following EP23 observability patterns.
"""

from __future__ import annotations

try:
    from prometheus_client import REGISTRY, Counter, Histogram

    _registry = REGISTRY

    voice_transcriptions_total = Counter(
        "voice_transcriptions_total",
        "Total number of voice transcription attempts.",
        ("status",),
        registry=_registry,
    )

    voice_transcription_duration_seconds = Histogram(
        "voice_transcription_duration_seconds",
        "Duration of voice transcription in seconds.",
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        registry=_registry,
    )

except ImportError:  # pragma: no cover - metrics optional for local runs

    class _DummyMetric:
        def labels(self, *args, **kwargs):  # type: ignore[override]
            return self

        def observe(self, *args, **kwargs):  # type: ignore
            return None

        def inc(self, *args, **kwargs):  # type: ignore[override]
            return None

    voice_transcriptions_total = _DummyMetric()  # type: ignore[assignment]
    voice_transcription_duration_seconds = _DummyMetric()  # type: ignore[assignment]


__all__ = [
    "voice_transcriptions_total",
    "voice_transcription_duration_seconds",
]
