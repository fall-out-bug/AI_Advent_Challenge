"""Prometheus metrics for benchmark data seeding."""

from __future__ import annotations

from prometheus_client import Counter

from src.application.benchmarking.seed_benchmark_data import BenchmarkSeedingMetrics

benchmark_digest_records_total = Counter(
    "benchmark_digest_records_total",
    "Number of digest records seeded per channel.",
    ["channel"],
)

benchmark_review_records_total = Counter(
    "benchmark_review_records_total",
    "Number of review reports seeded per channel.",
    ["channel"],
)


class PrometheusBenchmarkSeedingMetrics(BenchmarkSeedingMetrics):
    """Metrics adapter backed by Prometheus counters."""

    def record_digest_ingest(self, channel: str, inserted: int) -> None:
        """Record inserted digest count."""

        benchmark_digest_records_total.labels(channel=channel).inc(inserted)

    def record_review_report_ingest(self, channel: str, inserted: int) -> None:
        """Record inserted review report count."""

        benchmark_review_records_total.labels(channel=channel).inc(inserted)
