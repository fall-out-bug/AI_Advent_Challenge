"""Result types for Butler Agent use cases.

Following Clean Architecture: Use case results are typed, not raw dictionaries.
All result classes use Pydantic for validation and documentation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskCreationResult(BaseModel):
    """Result of task creation use case.

    Purpose:
        Typed result for task creation operations, replacing raw dictionaries.
        Supports both successful creation and clarification scenarios.

    Args:
        created: Whether task was successfully created
        task_id: Task ID if created successfully
        clarification: Clarification question if more info needed
        error: Error message if operation failed

    Example:
        TaskCreationResult(
            created=True,
            task_id="507f1f77bcf86cd799439011",
            clarification=None,
            error=None
        )
    """

    created: bool = Field(description="Whether task was successfully created")
    task_id: Optional[str] = Field(None, description="Task ID if created successfully")
    clarification: Optional[str] = Field(
        None, description="Clarification question if more info needed"
    )
    error: Optional[str] = Field(None, description="Error message if operation failed")


class DigestResult(BaseModel):
    """Result of channel digest collection use case.

    Purpose:
        Typed result for channel digest operations.

    Args:
        digests: List of channel digest dictionaries
        error: Error message if operation failed

    Example:
        DigestResult(
            digests=[
                {"channel_name": "python", "posts_count": 5, "summary": "..."}
            ],
            error=None
        )
    """

    digests: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of channel digest dictionaries"
    )
    error: Optional[str] = Field(None, description="Error message if operation failed")


class StatsResult(BaseModel):
    """Result of student statistics collection use case.

    Purpose:
        Typed result for student statistics operations.

    Args:
        stats: Dictionary with student statistics
        error: Error message if operation failed

    Example:
        StatsResult(
            stats={"total_students": 25, "active_students": 20},
            error=None
        )
    """

    stats: Dict[str, Any] = Field(
        default_factory=dict, description="Dictionary with student statistics"
    )
    error: Optional[str] = Field(None, description="Error message if operation failed")
