"""Prometheus metrics helpers for the MCP HTTP server."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator


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
    from prometheus_client import Counter, Gauge, Histogram  # type: ignore
except ImportError:  # pragma: no cover - fallback
    Counter = Gauge = Histogram = _DummyMetric  # type: ignore


MCP_REQUESTS_TOTAL = Counter(  # type: ignore[arg-type]
    "mcp_requests_total",
    "Total number of MCP tool invocations.",
    labelnames=("tool", "status"),
)

MCP_REQUEST_DURATION_SECONDS = Histogram(  # type: ignore[arg-type]
    "mcp_request_duration_seconds",
    "Latency of MCP tool invocations in seconds.",
    labelnames=("tool",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

MCP_TOOLS_REGISTERED = Gauge(  # type: ignore[arg-type]
    "mcp_tools_registered",
    "Number of MCP tools currently registered.",
)


def record_mcp_request(tool: str, status: str, duration_seconds: float) -> None:
    """Record a completed MCP tool invocation.

    Purpose:
        Emit Prometheus samples describing the result and duration of a single
        MCP tool call so alerts and dashboards can monitor behaviour.

    Args:
        tool: Name of the tool that was invoked.
        status: Outcome label such as ``success`` or ``error``.
        duration_seconds: Execution latency measured in seconds.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> record_mcp_request("list_models", "success", 0.42)
    """

    MCP_REQUESTS_TOTAL.labels(tool=tool, status=status).inc()
    MCP_REQUEST_DURATION_SECONDS.labels(tool=tool).observe(duration_seconds)


def set_registered_tools(count: int) -> None:
    """Set the gauge tracking the number of registered MCP tools.

    Purpose:
        Keep the Prometheus gauge in sync with the number of MCP tools that are
        available at runtime.

    Args:
        count: Total number of registered tools.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> set_registered_tools(6)
    """

    MCP_TOOLS_REGISTERED.set(count)


@contextmanager
def track_tool_request(tool: str) -> Generator[None, None, None]:
    """Context manager that times an MCP tool invocation.

    Purpose:
        Simplify timing logic for tool calls so that metrics are recorded even
        when exceptions interrupt execution.

    Args:
        tool: Name of the tool being executed.

    Returns:
        Generator yielding control to the wrapped block.

    Raises:
        Propagates any exception from the wrapped context.

    Example:
        >>> with track_tool_request("list_models"):
        ...     await some_async_call()
    """

    start = time.perf_counter()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.perf_counter() - start
        record_mcp_request(tool, status, duration)

