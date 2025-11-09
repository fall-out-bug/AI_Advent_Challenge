"""Centralized logging configuration and utilities.

Provides a unified interface for logging across the application.
Following the Zen of Python: Simple is better than complex.
"""

import logging
import sys
from typing import Optional

from src.infrastructure.config.settings import Settings
from src.infrastructure.logging.review_logger import ReviewLogger

__all__ = ["get_logger", "ReviewLogger"]


class StructuredLogger(logging.Logger):
    """Logger that moves arbitrary keyword arguments into `extra`."""

    _RESERVED_KWARGS = {"exc_info", "stack_info", "stacklevel", "extra"}

    def _log(self, level, msg, args, **kwargs):  # type: ignore[override]
        extra = kwargs.pop("extra", {}) or {}
        for key in list(kwargs.keys()):
            if key not in self._RESERVED_KWARGS:
                extra[key] = kwargs.pop(key)
        if extra:
            kwargs["extra"] = extra
        super()._log(level, msg, args, **kwargs)


# Ensure all future loggers use StructuredLogger
logging.setLoggerClass(StructuredLogger)


def get_logger(name: str, settings: Optional[Settings] = None) -> logging.Logger:
    """Get or create logger instance with centralized configuration.

    Args:
        name: Logger name (typically __name__ from calling module)
        settings: Optional settings instance. If None, uses get_settings().

    Returns:
        Configured logging.Logger instance
    """
    from src.infrastructure.config.settings import get_settings

    if settings is None:
        settings = get_settings()

    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Configure handler based on settings
    handler = logging.StreamHandler(sys.stderr)

    # Set log level from settings or default to INFO
    log_level = settings.log_level.upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    handler.setLevel(getattr(logging, log_level, logging.INFO))

    # Configure formatter
    if settings.log_format:
        formatter = logging.Formatter(settings.log_format)
    else:
        # Default format: timestamp, level, name, message
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False

    return logger
