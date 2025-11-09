"""Deprecated logging helpers retained for backwards compatibility."""

from __future__ import annotations

from warnings import warn

from src.infrastructure.logging import (
    get_logger,
    log_context,
    performance_timer,
    with_request_id,
)

warn(
    "src.infrastructure.monitoring.logger is deprecated; import from "
    "src.infrastructure.logging instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "get_logger",
    "log_context",
    "with_request_id",
    "performance_timer",
]
