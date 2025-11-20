"""Intent classification metrics for Prometheus.

Following the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
"""

try:
    from prometheus_client import Counter, Histogram  # type: ignore

    # Intent classification counts by type and source
    intent_classifications_total = Counter(
        "intent_classifications_total",
        "Total number of intent classifications",
        ["intent_type", "source"],  # source: "rule", "llm", "cached"
    )

    # Intent classification latency
    intent_classification_latency_seconds = Histogram(
        "intent_classification_latency_seconds",
        "Time spent classifying user intents",
        ["source"],  # source: "rule", "llm", "cached"
        buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    )

    # Cache metrics
    intent_cache_hits_total = Counter(
        "intent_cache_hits_total",
        "Total number of intent classification cache hits",
    )

    intent_cache_misses_total = Counter(
        "intent_cache_misses_total",
        "Total number of intent classification cache misses",
    )

    # LLM failures
    intent_llm_failures_total = Counter(
        "intent_llm_failures_total",
        "Total number of LLM classification failures",
        ["error_type"],
    )

except ImportError:
    # Metrics are optional - create dummy objects if prometheus_client not available
    class _DummyMetric:
        def inc(self, *args, **kwargs):  # type: ignore
            pass

        def observe(self, *args, **kwargs):  # type: ignore
            pass

        def labels(self, *args, **kwargs):  # type: ignore
            return self

    intent_classifications_total = _DummyMetric()
    intent_classification_latency_seconds = _DummyMetric()
    intent_cache_hits_total = _DummyMetric()
    intent_cache_misses_total = _DummyMetric()
    intent_llm_failures_total = _DummyMetric()


class IntentMetrics:
    """Intent classification metrics tracker.

    Wrapper for Prometheus metrics with convenience methods.
    """

    @staticmethod
    def record_classification(
        intent_type: str, source: str, latency_seconds: float
    ) -> None:
        """Record intent classification.

        Args:
            intent_type: Intent type (e.g., "TASK_CREATE", "DATA_DIGEST")
            source: Classification source ("rule", "llm", "cached")
            latency_seconds: Classification latency in seconds
        """
        intent_classifications_total.labels(
            intent_type=intent_type, source=source
        ).inc()
        intent_classification_latency_seconds.labels(source=source).observe(
            latency_seconds
        )

    @staticmethod
    def record_cache_hit() -> None:
        """Record cache hit."""
        intent_cache_hits_total.inc()

    @staticmethod
    def record_cache_miss() -> None:
        """Record cache miss."""
        intent_cache_misses_total.inc()

    @staticmethod
    def record_llm_failure(error_type: str = "unknown") -> None:
        """Record LLM classification failure.

        Args:
            error_type: Type of error (e.g., "timeout", "parse_error", "network_error")
        """
        intent_llm_failures_total.labels(error_type=error_type).inc()
