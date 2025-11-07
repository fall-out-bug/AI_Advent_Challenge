"""Task type enumeration for long-running tasks."""

from enum import Enum


class TaskType(str, Enum):
    """Type of long-running task.

    Purpose:
        Represents different types of asynchronous tasks that can be
        processed by the unified task worker. Allows the same repository
        and worker infrastructure to handle multiple task types.

    Values:
        SUMMARIZATION: Telegram channel digest generation
        CODE_REVIEW: Code review from ZIP archives
    """

    SUMMARIZATION = "summarization"
    CODE_REVIEW = "code_review"

