"""Prometheus metrics utilities for the unified task worker."""

from __future__ import annotations

from threading import Lock
from typing import Dict


class _DummyMetric:
    """Fallback metric used when prometheus_client is unavailable."""

    def labels(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Mirror the prometheus metric interface by returning self."""
        return self

    def inc(self, *args, **kwargs) -> None:
        """No-op increment method."""

    def observe(self, *args, **kwargs) -> None:
        """No-op observation method."""

    def set(self, *args, **kwargs) -> None:
        """No-op setter for gauge semantics."""


try:  # pragma: no cover - optional dependency guard
    from prometheus_client import (  # type: ignore
        Counter,
        Gauge,
        Histogram,
        start_http_server,
    )
except ImportError:  # pragma: no cover - fallback
    Counter = Gauge = Histogram = _DummyMetric  # type: ignore

    def start_http_server(*args, **kwargs):  # type: ignore[no-redef]
        """Fallback start_http_server that performs no action."""

        return None


UNIFIED_WORKER_TASKS_TOTAL = Counter(  # type: ignore[arg-type]
    "unified_worker_tasks_total",
    "Total number of tasks processed by the unified worker.",
    labelnames=("task_type", "status"),
)

UNIFIED_WORKER_TASK_DURATION_SECONDS = Histogram(  # type: ignore[arg-type]
    "unified_worker_task_duration_seconds",
    "Processing latency for unified worker tasks in seconds.",
    labelnames=("task_type",),
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

UNIFIED_WORKER_QUEUE_DEPTH = Gauge(  # type: ignore[arg-type]
    "unified_worker_queue_depth",
    "Approximate queue depth for unified worker tasks.",
    labelnames=("task_type",),
)

_METRICS_SERVER_STATE: Dict[int, bool] = {}
_METRICS_LOCK = Lock()


def record_worker_task(task_type: str, status: str, duration_seconds: float) -> None:
    """Record a completed task processed by the unified worker.

    Purpose:
        Emit Prometheus samples describing the outcome and duration of queued
        work handled by the unified worker (summaries, reviews, digests).

    Args:
        task_type: Logical type of the task (for example, ``summarization``).
        status: Outcome label such as ``success`` or ``error``.
        duration_seconds: Execution latency measured in seconds.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> record_worker_task("summarization", "success", 12.5)
    """

    UNIFIED_WORKER_TASKS_TOTAL.labels(task_type=task_type, status=status).inc()
    UNIFIED_WORKER_TASK_DURATION_SECONDS.labels(task_type=task_type).observe(
        duration_seconds
    )


def set_worker_queue_depth(task_type: str, depth: int) -> None:
    """Set the queue depth gauge for a given task type.

    Purpose:
        Provide visibility into outstanding work by exposing the number of
        queued tasks awaiting processing.

    Args:
        task_type: Logical task type identifier.
        depth: The number of tasks currently queued.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> set_worker_queue_depth("code_review", 7)
    """

    UNIFIED_WORKER_QUEUE_DEPTH.labels(task_type=task_type).set(depth)


def start_worker_metrics_server(port: int = 9092) -> None:
    """Start an HTTP server that exposes worker metrics.

    Purpose:
        Serve Prometheus metrics for the unified worker on the specified port
        while avoiding duplicate server start attempts when the function is
        called multiple times.

    Args:
        port: TCP port for the metrics server (default: 9092).

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> start_worker_metrics_server(9092)
    """

    with _METRICS_LOCK:
        if _METRICS_SERVER_STATE.get(port):
            return
        start_http_server(port)  # type: ignore[arg-type]
        _METRICS_SERVER_STATE[port] = True
