"""Prometheus metrics for Day 12 features.

Following the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram  # type: ignore

    # Post Fetcher Worker Metrics
    post_fetcher_posts_saved_total = Counter(
        "post_fetcher_posts_saved_total",
        "Total number of posts saved by post fetcher",
        ["channel_username"],
    )

    post_fetcher_channels_processed_total = Counter(
        "post_fetcher_channels_processed_total",
        "Total number of channels processed by post fetcher",
    )

    post_fetcher_errors_total = Counter(
        "post_fetcher_errors_total",
        "Total number of errors in post fetcher",
        ["error_type"],
    )

    post_fetcher_duration_seconds = Histogram(
        "post_fetcher_duration_seconds",
        "Time spent processing channels in post fetcher",
        buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    )

    post_fetcher_posts_skipped_total = Counter(
        "post_fetcher_posts_skipped_total",
        "Total number of posts skipped (duplicates) by post fetcher",
        ["channel_username"],
    )

    # PDF Generation Metrics
    pdf_generation_duration_seconds = Histogram(
        "pdf_generation_duration_seconds",
        "Time spent generating PDF digests",
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    pdf_generation_errors_total = Counter(
        "pdf_generation_errors_total",
        "Total number of PDF generation errors",
        ["error_type"],
    )

    pdf_file_size_bytes = Histogram(
        "pdf_file_size_bytes",
        "Size of generated PDF files in bytes",
        buckets=[10000, 50000, 100000, 500000, 1000000, 5000000],
    )

    pdf_pages_total = Histogram(
        "pdf_pages_total",
        "Number of pages in generated PDF files",
        buckets=[1, 2, 5, 10, 20, 50],
    )

    # Bot Digest Handler Metrics
    bot_digest_requests_total = Counter(
        "bot_digest_requests_total",
        "Total number of digest requests from bot",
    )

    bot_digest_cache_hits_total = Counter(
        "bot_digest_cache_hits_total",
        "Total number of cache hits for digest requests",
    )

    bot_digest_errors_total = Counter(
        "bot_digest_errors_total",
        "Total number of errors in digest handler",
        ["error_type"],
    )

    # Worker Health Metrics
    post_fetcher_worker_running = Gauge(
        "post_fetcher_worker_running",
        "Whether post fetcher worker is running (1) or stopped (0)",
    )

    post_fetcher_last_run_timestamp = Gauge(
        "post_fetcher_last_run_timestamp_seconds",
        "Unix timestamp of last post fetcher run",
    )

except ImportError:
    # Metrics are optional - create dummy objects if prometheus_client not available
    class _DummyMetric:
        def inc(self, *args, **kwargs):  # type: ignore
            pass

        def observe(self, *args, **kwargs):  # type: ignore
            pass

        def set(self, *args, **kwargs):  # type: ignore
            pass

        def labels(self, *args, **kwargs):  # type: ignore
            return self

        def time(self):  # type: ignore
            from contextlib import contextmanager

            @contextmanager
            def noop():
                yield

            return noop()

    post_fetcher_posts_saved_total = _DummyMetric()
    post_fetcher_channels_processed_total = _DummyMetric()
    post_fetcher_errors_total = _DummyMetric()
    post_fetcher_duration_seconds = _DummyMetric()
    post_fetcher_posts_skipped_total = _DummyMetric()
    pdf_generation_duration_seconds = _DummyMetric()
    pdf_generation_errors_total = _DummyMetric()
    pdf_file_size_bytes = _DummyMetric()
    pdf_pages_total = _DummyMetric()
    bot_digest_requests_total = _DummyMetric()
    bot_digest_cache_hits_total = _DummyMetric()
    bot_digest_errors_total = _DummyMetric()
    post_fetcher_worker_running = _DummyMetric()
    post_fetcher_last_run_timestamp = _DummyMetric()


def get_metrics_registry() -> Optional[object]:
    """Get Prometheus metrics registry.

    Returns:
        Registry object or None if prometheus_client not available
    """
    try:
        from prometheus_client import REGISTRY  # type: ignore

        return REGISTRY
    except ImportError:
        return None
