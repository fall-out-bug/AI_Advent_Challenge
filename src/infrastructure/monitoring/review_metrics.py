"""Prometheus metrics for review system."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# Review task metrics
review_tasks_total = Counter(
    "review_tasks_total",
    "Total number of review tasks",
    ["status"],  # queued, running, succeeded, failed
)

review_task_duration = Histogram(
    "review_task_duration_seconds",
    "Time spent processing review tasks",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

review_queue_size = Gauge(
    "review_queue_size",
    "Number of tasks in review queue",
)

review_llm_calls_total = Counter(
    "review_llm_calls_total",
    "Total number of LLM calls for reviews",
    ["status"],  # success, failure
)

review_llm_duration = Histogram(
    "review_llm_duration_seconds",
    "Time spent on LLM calls for reviews",
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120],
)

review_archive_extractions_total = Counter(
    "review_archive_extractions_total",
    "Total number of archive extractions",
    ["status"],  # success, failure
)

review_archive_size_bytes = Histogram(
    "review_archive_size_bytes",
    "Size of extracted archives in bytes",
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600],
)

review_external_api_publishes_total = Counter(
    "review_external_api_publishes_total",
    "Total number of external API publishes",
    ["status"],  # success, failure
)
