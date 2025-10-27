"""Simple metrics tracking infrastructure.

Following the Zen of Python:
- Simple is better than complex
- Practicality beats purity
- Readability counts
"""

import json
import statistics
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class MetricsCollector:
    """
    Simple in-memory metrics collector.

    Tracks request counters, token usage, error rates, and response times.
    """

    def __init__(self, rolling_window_size: int = 1000):
        """Initialize metrics collector.

        Args:
            rolling_window_size: Size of rolling window for time-series
        """
        self._lock = threading.Lock()
        self._rolling_window_size = rolling_window_size
        self._reset()

    def _reset(self) -> None:
        """Reset all metrics."""
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        self.total_response_time_ms = 0.0

        # Detailed tracking
        self.error_counts = defaultdict(int)
        self.operation_times: List[Dict[str, Any]] = []
        self.token_usage_by_operation: Dict[str, int] = defaultdict(int)

        # Time-series data (rolling window)
        self.response_times: deque = deque(maxlen=self._rolling_window_size)

        # Timestamps
        self.start_time = datetime.utcnow()
        self.last_reset = datetime.utcnow()

    def record_request(
        self,
        success: bool = True,
        tokens_used: int = 0,
        response_time_ms: float = 0.0,
        operation: str = "unknown",
        error: Optional[str] = None,
    ) -> None:
        """Record a request.

        Args:
            success: Whether request was successful
            tokens_used: Number of tokens used
            response_time_ms: Response time in milliseconds
            operation: Operation name
            error: Error message if failed
        """
        with self._lock:
            self.request_count += 1

            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                if error:
                    self.error_counts[error] += 1

            self.total_tokens_used += tokens_used
            self.total_response_time_ms += response_time_ms

            # Track response times in rolling window
            if response_time_ms > 0:
                self.response_times.append(response_time_ms)

            self.operation_times.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "operation": operation,
                    "response_time_ms": response_time_ms,
                    "success": success,
                }
            )

            if tokens_used > 0:
                self.token_usage_by_operation[operation] += tokens_used

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.

        Returns:
            Dictionary with current metrics
        """
        with self._lock:
            avg_response_time = 0.0
            if self.request_count > 0:
                avg_response_time = self.total_response_time_ms / self.request_count

            success_rate = 0.0
            if self.request_count > 0:
                success_rate = self.successful_requests / self.request_count

            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()

            # Get percentiles
            percentiles = self._calculate_percentiles()

            return {
                "request_count": self.request_count,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": success_rate,
                "total_tokens_used": self.total_tokens_used,
                "average_response_time_ms": avg_response_time,
                "total_response_time_ms": self.total_response_time_ms,
                "response_time_percentiles": percentiles,
                "error_counts": dict(self.error_counts),
                "uptime_seconds": uptime_seconds,
                "start_time": self.start_time.isoformat(),
                "last_reset": self.last_reset.isoformat(),
                "token_usage_by_operation": dict(self.token_usage_by_operation),
            }

    def _calculate_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles (internal method).

        Returns:
            Dictionary with p50, p95, p99 percentiles
        """
        if not self.response_times:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_times = sorted(self.response_times)

        def get_percentile(data: List[float], percentile: float) -> float:
            """Calculate percentile value."""
            if not data:
                return 0.0
            index = int(len(data) * percentile / 100)
            return data[min(index, len(data) - 1)]

        return {
            "p50": get_percentile(sorted_times, 50),
            "p95": get_percentile(sorted_times, 95),
            "p99": get_percentile(sorted_times, 99),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._reset()

    def export_to_file(self, filepath: str) -> None:
        """Export metrics to JSON file.

        Args:
            filepath: Path to output file
        """
        metrics = self.get_metrics()

        with Path(filepath).open("w") as f:
            json.dump(metrics, f, indent=2, default=str)

    def get_recent_operations(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get recent operations.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of recent operations
        """
        with self._lock:
            return self.operation_times[-limit:]

    def get_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles.

        Returns:
            Dictionary with p50, p95, p99 percentiles
        """
        with self._lock:
            return self._calculate_percentiles()


# Global metrics instance
_metrics_collector = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get global metrics collector.

    Returns:
        Metrics collector instance
    """
    return _metrics_collector


def record_request(**kwargs) -> None:
    """Record a request (convenience function).

    Args:
        **kwargs: Arguments to pass to record_request
    """
    _metrics_collector.record_request(**kwargs)
