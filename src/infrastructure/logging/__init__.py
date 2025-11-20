"""Centralised logging utilities with structured context support."""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from src.infrastructure.config.settings import Settings
from src.infrastructure.logging.review_logger import ReviewLogger

try:
    from src.infrastructure.metrics.observability_metrics import structured_logs_total
except Exception:  # pragma: no cover - metrics optional in constrained envs
    structured_logs_total = None
__all__ = [
    "get_logger",
    "ReviewLogger",
    "log_context",
    "with_request_id",
    "performance_timer",
]

_LOG_CONTEXT: ContextVar[Dict[str, str]] = ContextVar("log_context", default={})

_SENSITIVE_KEYWORDS = {
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "credential",
    "access_token",
    "refresh_token",
}
_PII_KEYWORDS = {"email", "phone", "user_email"}
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _mask_email(value: str) -> str:
    local, _, domain = value.partition("@")
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    return f"{masked_local}@{domain}"


def _sanitize_value(key: str, value: object) -> object:
    lower_key = key.lower()
    if lower_key in _SENSITIVE_KEYWORDS:
        return "***REDACTED***"
    if isinstance(value, str):
        if any(keyword in lower_key for keyword in _PII_KEYWORDS):
            return _mask_email(value) if "@" in value else "***REDACTED***"
        if _EMAIL_RE.search(value):
            return _EMAIL_RE.sub(lambda match: _mask_email(match.group(0)), value)
    if isinstance(value, dict):
        return {k: _sanitize_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(key, item) for item in value]
    return value


def _sanitize_payload(payload: Dict[str, object]) -> Dict[str, object]:
    return {k: _sanitize_value(k, v) for k, v in payload.items()}


class StructuredFormatter(logging.Formatter):
    """Formatter that renders logs as JSON or enriched text."""

    def __init__(self, json_logs: bool, *, datefmt: str) -> None:
        super().__init__(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt=datefmt,
        )
        self._json_logs = json_logs

    def format(self, record: logging.LogRecord) -> str:
        structured_data = getattr(record, "structured_data", None)
        if self._json_logs:
            payload = structured_data or {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if structured_data is None:
                payload.update(_LOG_CONTEXT.get({}))
            return json.dumps(payload, default=str)

        message = super().format(record)
        if structured_data:
            extra = {
                key: value
                for key, value in structured_data.items()
                if key not in {"message", "level", "timestamp"}
            }
            if extra:
                return f"{message} | {extra}"
        return message


class StructuredLogger(logging.Logger):
    """Logger that promotes keyword arguments into structured metadata."""

    _RESERVED_KWARGS = {"exc_info", "stack_info", "stacklevel", "extra"}

    def _log(self, level, msg, args, **kwargs):  # type: ignore[override]
        extra_payload = kwargs.pop("extra", {}) or {}
        structured: Dict[str, object] = (
            dict(extra_payload) if isinstance(extra_payload, dict) else {}
        )

        for key in list(kwargs.keys()):
            if key not in self._RESERVED_KWARGS:
                structured[key] = kwargs.pop(key)

        structured.setdefault("message", msg)
        structured.setdefault("level", logging.getLevelName(level))
        structured.setdefault("timestamp", datetime.utcnow().isoformat())
        structured.update(_LOG_CONTEXT.get({}))

        if structured_logs_total:
            try:
                structured_logs_total.labels(
                    service=self.name, level=logging.getLevelName(level).lower()
                ).inc()
            except Exception:  # pragma: no cover - defensive logging
                pass

        kwargs["extra"] = {"structured_data": _sanitize_payload(structured)}
        super()._log(level, msg, args, **kwargs)


logging.setLoggerClass(StructuredLogger)


def _should_use_json(settings: Settings, enable_json: Optional[bool]) -> bool:
    """Determine whether JSON logging should be enabled."""

    if enable_json is not None:
        return enable_json
    fmt = (settings.log_format or "").lower()
    return fmt == "json"


def get_logger(
    name: str,
    settings: Optional[Settings] = None,
    *,
    enable_json: Optional[bool] = None,
) -> logging.Logger:
    """Initialise or return a configured logger instance.

    Purpose:
        Provide a single entry point for obtaining structured loggers across
        the codebase, ensuring consistent formatting and context propagation.

    Args:
        name: Logger name, typically ``__name__`` of the caller.
        settings: Optional settings instance used to derive defaults.
        enable_json: Overrides the JSON logging flag derived from settings when
            provided.

    Returns:
        Configured ``logging.Logger`` instance.

    Raises:
        None.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("worker_started", worker="unified-task-worker")
    """

    from src.infrastructure.config.settings import get_settings

    resolved_settings = settings or get_settings()
    json_logs = _should_use_json(resolved_settings, enable_json)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stderr)
    log_level = resolved_settings.log_level.upper()
    handler.setLevel(getattr(logging, log_level, logging.INFO))

    date_format = getattr(resolved_settings, "log_datefmt", None) or "%Y-%m-%d %H:%M:%S"

    formatter = StructuredFormatter(
        json_logs=json_logs,
        datefmt=date_format,
    )
    handler.setFormatter(formatter)

    logger.setLevel(getattr(logging, log_level, logging.INFO))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


@contextmanager
def log_context(**kwargs: str) -> None:
    """Push contextual fields for subsequent log records.

    Purpose:
        Attach metadata such as ``request_id`` or ``user_id`` to all log entries
        within the managed scope.

    Args:
        **kwargs: Key/value pairs to merge into the logging context.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> with log_context(request_id="abc123"):
        ...     logger.info("Processing request")
    """

    filtered = {k: v for k, v in kwargs.items() if v is not None}
    token = _LOG_CONTEXT.set({**_LOG_CONTEXT.get({}), **filtered})
    try:
        yield
    finally:
        _LOG_CONTEXT.reset(token)


@contextmanager
def with_request_id(request_id: Optional[str] = None) -> None:
    """Attach a request identifier to the logging context.

    Purpose:
        Generate or reuse a request identifier for correlating logs across
        service boundaries.

    Args:
        request_id: Optional explicit request identifier. When omitted a new
            UUIDv4 hex value is generated.

    Returns:
        None.

    Raises:
        None.

    Example:
        >>> with with_request_id():
        ...     logger.info("Handling inbound HTTP request")
    """

    generated = request_id or uuid4().hex
    with log_context(request_id=generated):
        yield


@contextmanager
def performance_timer(logger: logging.Logger, operation: str) -> None:
    """Measure and log execution time for a code block.

    Purpose:
        Provide a reusable context manager for emitting performance telemetry
        while capturing success or failure state.

    Args:
        logger: Logger instance obtained via :func:`get_logger`.
        operation: Human-readable operation identifier.

    Returns:
        None.

    Raises:
        Re-raises any exception thrown inside the managed block.

    Example:
        >>> with performance_timer(logger, "fetch_data"):
        ...     fetch_from_external_service()
    """

    start = time.perf_counter()
    success = True
    try:
        yield
    except Exception:  # noqa: BLE001 - re-raise after logging
        success = False
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "operation_complete",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            success=success,
        )
