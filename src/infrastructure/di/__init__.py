"""Dependency injection container and factories."""

from __future__ import annotations

from .container import SummarizationContainer
from .factories import (
    create_adaptive_summarizer,
    create_channel_digest_by_name_use_case,
    create_channel_digest_use_case,
    create_task_summary_use_case,
)

__all__ = [
    "SummarizationContainer",
    "create_adaptive_summarizer",
    "create_task_summary_use_case",
    "create_channel_digest_use_case",
    "create_channel_digest_by_name_use_case",
]
