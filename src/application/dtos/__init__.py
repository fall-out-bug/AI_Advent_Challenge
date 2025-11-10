"""Data transfer objects for use cases."""

from __future__ import annotations

from .digest_dtos import ChannelDigest, TaskSummaryResult
from .homework_dtos import (
    HomeworkListResult,
    HomeworkReviewResult,
    HomeworkSubmission,
)
from .butler_dialog_dtos import DialogContext, DialogMode, DialogState

__all__ = [
    "ChannelDigest",
    "TaskSummaryResult",
    "HomeworkSubmission",
    "HomeworkListResult",
    "HomeworkReviewResult",
    "DialogMode",
    "DialogState",
    "DialogContext",
]
