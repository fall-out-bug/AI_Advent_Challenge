"""Structured logging infrastructure.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Beautiful is better than ugly
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


class StructuredLogger:
    """
    Structured logger with JSON output and request tracking.

    Provides structured logging with request IDs and performance tracking.
    """

    def __init__(
        self,
        name: str = "ai_challenge",
        level: str = "INFO",
        enable_json: bool = True,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_json: Enable JSON output formatting
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, level.upper()))

        if enable_json:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.enable_json = enable_json

    def _log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """Log a message with structured data.

        Args:
            level: Log level
            message: Log message
            extra: Additional structured data
            **kwargs: Additional fields to include in log
        """
        log_data = {
            "message": message,
            "level": level,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if extra:
            log_data.update(extra)

        log_data.update(kwargs)

        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra={"structured": log_data})

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log("CRITICAL", message, **kwargs)

    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        **kwargs,
    ) -> None:
        """Log performance metrics.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            **kwargs: Additional performance metrics
        """
        self.info(
            f"Performance: {operation}",
            operation=operation,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Log HTTP request.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            request_id: Request ID for tracing
            **kwargs: Additional request data
        """
        log_data = {
            "type": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "request_id": request_id or str(uuid4()),
            **kwargs,
        }

        self.info(f"{method} {path} - {status_code}", **log_data)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON formatted log string
        """
        if hasattr(record, "structured"):
            return json.dumps(record.structured, default=str)

        # Fallback to standard format
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        return json.dumps(data, default=str)


class PerformanceTracker:
    """Context manager for tracking performance."""

    def __init__(self, logger: StructuredLogger, operation: str):
        """Initialize performance tracker.

        Args:
            logger: Logger instance
            operation: Operation name
        """
        self.logger = logger
        self.operation = operation
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start tracking."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End tracking and log performance."""
        if self.start_time:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.logger.log_performance(
                self.operation,
                duration_ms,
                success=exc_type is None,
            )


# Global logger instance
def get_logger(name: str = "ai_challenge") -> StructuredLogger:
    """Get or create logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return StructuredLogger(name=name)
