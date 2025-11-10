"""Prometheus metrics utilities for backoffice CLI."""

from __future__ import annotations

from .prometheus import (
    cli_command_duration_seconds,
    cli_command_errors_total,
    cli_command_total,
    track_command,
)

__all__ = [
    "cli_command_total",
    "cli_command_duration_seconds",
    "cli_command_errors_total",
    "track_command",
]

