"""Task status enumeration for async operations."""

from enum import Enum


class TaskStatus(str, Enum):
    """Status of a long-running task.

    Purpose:
        Represents the lifecycle state of asynchronous tasks.
        Used for tracking task progress and coordination between
        components.

    Values:
        QUEUED: Task created and waiting for processing
        RUNNING: Task currently being processed
        SUCCEEDED: Task completed successfully
        FAILED: Task failed with error
    """

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

