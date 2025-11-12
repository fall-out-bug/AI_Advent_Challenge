"""Prometheus instrumentation for backoffice CLI."""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Awaitable, Callable, TypeVar

from prometheus_client import Counter, Histogram

cli_command_total = Counter(
    "cli_command_total",
    "Total number of executed CLI commands",
    ("command", "status"),
)
cli_command_duration_seconds = Histogram(
    "cli_command_duration_seconds",
    "CLI command execution duration in seconds",
    ("command",),
)
cli_command_errors_total = Counter(
    "cli_command_errors_total",
    "Total number of CLI command errors",
    ("command", "error_type"),
)

F = TypeVar("F", bound=Callable[..., Any])


def track_command(command_name: str) -> Callable[[F], F]:
    """Instrument a CLI command with Prometheus metrics."""

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001 - we re-raise after logging
                    _record_error(command_name, exc, start_time)
                    raise
                _record_success(command_name, start_time)
                return result

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                _record_error(command_name, exc, start_time)
                raise
            _record_success(command_name, start_time)
            return result

        return sync_wrapper  # type: ignore[return-value]

    return decorator


def _record_success(command: str, start_time: float) -> None:
    """Record successful command execution."""
    cli_command_total.labels(command=command, status="success").inc()
    cli_command_duration_seconds.labels(command=command).observe(
        time.perf_counter() - start_time
    )


def _record_error(command: str, exc: Exception, start_time: float) -> None:
    """Record failed command execution."""
    cli_command_total.labels(command=command, status="error").inc()
    cli_command_errors_total.labels(
        command=command, error_type=exc.__class__.__name__
    ).inc()
    cli_command_duration_seconds.labels(command=command).observe(
        time.perf_counter() - start_time
    )
