"""
Structured logging utilities for Token Analysis System.

This module provides structured logging functionality
with JSON formatting and request tracking.

Example:
    Basic logging setup:
    
    ```python
    from utils.logging import LoggerFactory
    
    # Create logger
    logger = LoggerFactory.create_logger("my_module")
    
    # Log structured data
    logger.info("Processing request", 
                request_id="123", 
                model="starcoder", 
                tokens=150)
    
    # Log errors with context
    logger.error("Token limit exceeded", 
                 model="starcoder", 
                 tokens=5000, 
                 limit=4096)
    ```
    
    Advanced logging configuration:
    
    ```python
    # Create logger with custom configuration
    logger = LoggerFactory.create_logger(
        name="experiments",
        level="DEBUG",
        format_type="json"
    )
    
    # Log experiment results
    logger.info("Experiment completed",
                experiment="compression_test",
                success=True,
                compression_ratio=0.3)
    ```
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from core.interfaces.protocols import LoggerProtocol


class StructuredLogger:
    """Structured logger implementation."""

    def __init__(self, name: str, level: str = "WARNING", format_type: str = "json"):
        """Initialize structured logger."""
        self.name = name
        self.level = level
        self.format_type = format_type
        self._logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with configuration."""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.level.upper()))

        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)

        # Set formatter based on type
        if self.format_type == "json":
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Prevent duplicate logs
        logger.propagate = False

        return logger

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal logging method."""
        extra = kwargs if kwargs else {}
        self._logger.log(level, message, extra=extra)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        from datetime import datetime

        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


class RequestLogger:
    """Logger with request tracking capabilities."""

    def __init__(self, logger: StructuredLogger):
        """Initialize request logger."""
        self.logger = logger
        self.request_id: Optional[str] = None

    def set_request_id(self, request_id: str) -> None:
        """Set request ID for tracking."""
        self.request_id = request_id

    def log_request_start(self, method: str, url: str, **kwargs: Any) -> None:
        """Log request start."""
        self.logger.info(
            "request_start",
            request_id=self.request_id,
            method=method,
            url=url,
            **kwargs,
        )

    def log_request_end(self, status_code: int, duration: float, **kwargs: Any) -> None:
        """Log request end."""
        self.logger.info(
            "request_end",
            request_id=self.request_id,
            status_code=status_code,
            duration=duration,
            **kwargs,
        )

    def log_request_error(self, error: str, **kwargs: Any) -> None:
        """Log request error."""
        self.logger.error(
            "request_error", request_id=self.request_id, error=error, **kwargs
        )


class LoggerFactory:
    """Factory for creating loggers."""

    @staticmethod
    def create_logger(
        name: str, level: str = "WARNING", format_type: str = "json"
    ) -> StructuredLogger:
        """Create structured logger."""
        return StructuredLogger(name, level, format_type)

    @staticmethod
    def create_request_logger(
        name: str, level: str = "WARNING", format_type: str = "json"
    ) -> RequestLogger:
        """Create request logger."""
        logger = LoggerFactory.create_logger(name, level, format_type)
        return RequestLogger(logger)

    @staticmethod
    def setup_root_logger(level: str = "WARNING", format_type: str = "json") -> None:
        """Setup root logger configuration."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )


# Global logger instances
def get_logger(name: str) -> StructuredLogger:
    """Get logger instance."""
    return LoggerFactory.create_logger(name)


def get_request_logger(name: str) -> RequestLogger:
    """Get request logger instance."""
    return LoggerFactory.create_request_logger(name)
