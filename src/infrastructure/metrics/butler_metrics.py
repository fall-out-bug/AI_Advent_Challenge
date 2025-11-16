"""Butler Agent Prometheus metrics definitions.

Purpose:
    Define all Prometheus metrics for Butler Agent monitoring.
    Includes counters, histograms, and gauges for message processing,
    handler invocations, errors, and mode classifications.

Following Clean Architecture: Infrastructure layer metrics.
Following Python Zen: Simple, explicit, readable.
"""

import time
from contextlib import contextmanager
from typing import Optional

from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.prometheus_metrics import get_metrics_registry

logger = get_logger("butler_metrics")

try:
    from prometheus_client import Counter, Gauge, Histogram, REGISTRY

    _butler_registry = REGISTRY
except ImportError:  # pragma: no cover - metrics are optional

    class _DummyMetric:
        def labels(self, *args, **kwargs):  # type: ignore[override]
            return self

        def observe(self, *args, **kwargs):  # type: ignore[override]
            return None

        def inc(self, *args, **kwargs):  # type: ignore[override]
            return None

        def set(self, *args, **kwargs):  # type: ignore[override]
            return None

    Counter = Histogram = Gauge = lambda *args, **kwargs: _DummyMetric()  # type: ignore[assignment]
    _butler_registry = None

# =============================================
# Counter Metrics
# =============================================

butler_messages_total = Counter(
    "butler_messages_total",
    "Total messages processed by Butler Agent",
    ["status"],  # status: success, error
    registry=_butler_registry,
)

butler_errors_total = Counter(
    "butler_errors_total",
    "Total errors encountered by Butler Agent",
    ["error_type", "handler"],  # error_type: timeout, connection, validation, etc.
    registry=_butler_registry,
)

butler_mode_classifications_total = Counter(
    "butler_mode_classifications_total",
    "Total mode classifications performed",
    ["mode"],  # mode: TASK, DATA, IDLE
    registry=_butler_registry,
)

butler_handler_invocations_total = Counter(
    "butler_handler_invocations_total",
    "Total handler invocations by handler type",
    ["handler_type", "status"],  # handler_type: task, data, chat
    registry=_butler_registry,
)

# =============================================
# Histogram Metrics
# =============================================

butler_message_duration_seconds = Histogram(
    "butler_message_duration_seconds",
    "Message processing duration in seconds",
    ["mode", "handler_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],  # Up to 30 seconds
    registry=_butler_registry,
)

butler_llm_classification_duration_seconds = Histogram(
    "butler_llm_classification_duration_seconds",
    "LLM mode classification duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
    registry=_butler_registry,
)

butler_mongodb_query_duration_seconds = Histogram(
    "butler_mongodb_query_duration_seconds",
    "MongoDB query duration in seconds",
    ["operation"],  # operation: get_context, save_context
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
    registry=_butler_registry,
)

# =============================================
# Gauge Metrics
# =============================================

butler_active_users = Gauge(
    "butler_active_users",
    "Number of active users (unique in last hour)",
    registry=_butler_registry,
)

butler_bot_healthy = Gauge(
    "butler_bot_healthy",
    "Butler bot health status (1 = healthy, 0 = unhealthy)",
    registry=_butler_registry,
)


class ButlerMetrics:
    """Metrics collector for Butler Agent operations.

    Purpose:
        Provides convenient methods for recording Butler Agent metrics.
        Automatically handles labels and error tracking.

    Example:
        >>> metrics = ButlerMetrics()
        >>> with metrics.record_message_processing(mode="TASK"):
        ...     # Process message
        ...     pass
    """

    def __init__(self, registry: Optional[object] = None) -> None:
        """Initialize Butler metrics collector."""
        self.registry = registry or _butler_registry

    @contextmanager
    def record_message_processing(self, mode: str, handler_type: str) -> None:
        """Record message processing duration and success/error.

        Args:
            mode: Dialog mode (TASK, DATA, IDLE)
            handler_type: Handler type (task, data, chat)

        Example:
            >>> with metrics.record_message_processing(mode="TASK", handler_type="task"):
            ...     await handler.handle(context, message)
        """
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            butler_message_duration_seconds.labels(
                mode=mode, handler_type=handler_type
            ).observe(duration)
            butler_messages_total.labels(status="success").inc()
            butler_handler_invocations_total.labels(
                handler_type=handler_type, status="success"
            ).inc()
        except Exception as e:
            duration = time.time() - start_time
            butler_message_duration_seconds.labels(
                mode=mode, handler_type=handler_type
            ).observe(duration)
            butler_messages_total.labels(status="error").inc()
            butler_handler_invocations_total.labels(
                handler_type=handler_type, status="error"
            ).inc()
            error_type = type(e).__name__
            butler_errors_total.labels(
                error_type=error_type, handler=handler_type
            ).inc()
            raise

    def record_mode_classification(self, mode: str) -> None:
        """Record mode classification.

        Args:
            mode: Classified mode (TASK, DATA, IDLE)
        """
        butler_mode_classifications_total.labels(mode=mode).inc()

    def record_llm_classification_duration(self, duration: float) -> None:
        """Record LLM classification duration.

        Args:
            duration: Duration in seconds
        """
        butler_llm_classification_duration_seconds.observe(duration)

    @contextmanager
    def record_mongodb_operation(self, operation: str) -> None:
        """Record MongoDB operation duration.

        Args:
            operation: Operation name (get_context, save_context)

        Example:
            >>> with metrics.record_mongodb_operation("get_context"):
            ...     context = await mongodb.dialog_contexts.find_one(...)
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            butler_mongodb_query_duration_seconds.labels(operation=operation).observe(
                duration
            )

    def record_error(self, error_type: str, handler: str) -> None:
        """Record an error.

        Args:
            error_type: Type of error (TimeoutError, ConnectionError, etc.)
            handler: Handler where error occurred
        """
        butler_errors_total.labels(error_type=error_type, handler=handler).inc()

    def set_active_users(self, count: int) -> None:
        """Set active users count.

        Args:
            count: Number of active users
        """
        butler_active_users.set(count)

    def set_health_status(self, healthy: bool) -> None:
        """Set bot health status.

        Args:
            healthy: True if bot is healthy, False otherwise
        """
        butler_bot_healthy.set(1 if healthy else 0)

    def get_registry(self) -> Optional[object]:
        """Get metrics registry.

        Returns:
            Prometheus CollectorRegistry instance
        """
        return self.registry


# Global metrics instance
_butler_metrics_instance: Optional[ButlerMetrics] = None


def get_butler_metrics() -> ButlerMetrics:
    """Get global Butler metrics instance.

    Returns:
        Singleton ButlerMetrics instance
    """
    global _butler_metrics_instance
    if _butler_metrics_instance is None:
        _butler_metrics_instance = ButlerMetrics(get_metrics_registry())
    return _butler_metrics_instance
