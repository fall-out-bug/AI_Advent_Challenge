"""DTOs for Butler legacy task and data use cases."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskCreationResult(BaseModel):
    """Result of task creation use case.

    Purpose:
        Provide a typed container for task creation outcomes, covering
        successful creation, clarification follow-ups, and failures.

    Args:
        created: Whether the task was created successfully.
        task_id: Identifier of the created task.
        clarification: Clarification question to ask the user.
        error: Error description when creation fails.

    Example:
        >>> TaskCreationResult(created=True, task_id="42")
        TaskCreationResult(created=True, task_id='42', clarification=None, error=None)
    """

    created: bool = Field(description="Whether the task was created successfully.")
    task_id: Optional[str] = Field(
        default=None, description="Identifier of the created task."
    )
    clarification: Optional[str] = Field(
        default=None, description="Clarification question to ask the user."
    )
    error: Optional[str] = Field(
        default=None, description="Error description when creation fails."
    )
    intent_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Serialized intent payload for follow-up interactions.",
    )


class DigestResult(BaseModel):
    """Result of channel digest retrieval.

    Purpose:
        Represent the outcome of channel digest collection, encapsulating
        both successful payloads and failures in a structured way.

    Args:
        digests: List of channel digest dictionaries.
        error: Error message when the retrieval fails.

    Example:
        >>> DigestResult(digests=[{"channel": "python"}])
        DigestResult(digests=[{'channel': 'python'}], error=None)
    """

    digests: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of channel digest dictionaries."
    )
    error: Optional[str] = Field(
        default=None, description="Error message when retrieval fails."
    )


class StatsResult(BaseModel):
    """Result of student statistics retrieval.

    Purpose:
        Provide a typed result for student statistics queries, capturing both
        numerical data and potential errors without exposing raw tool output.

    Args:
        stats: Student statistics dictionary.
        error: Error message when the operation fails.

    Example:
        >>> StatsResult(stats={"students": 10})
        StatsResult(stats={'students': 10}, error=None)
    """

    stats: Dict[str, Any] = Field(
        default_factory=dict, description="Student statistics dictionary."
    )
    error: Optional[str] = Field(
        default=None, description="Error message when retrieval fails."
    )
