"""SkillResult domain entity."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class SkillResultStatus(str, Enum):
    """Skill result status enumeration.

    Purpose:
        Represents the outcome status of skill execution.

    Values:
        SUCCESS: Skill executed successfully
        FAILURE: Skill execution failed
    """

    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class SkillResult:
    """Skill result domain entity.

    Purpose:
        Represents the result of skill execution with status, output,
        errors, and metadata.

    Attributes:
        result_id: Unique identifier for the result.
        status: Result status (SUCCESS or FAILURE).
        output: Output data (required for SUCCESS).
        error: Error message (required for FAILURE).
        metadata: Optional metadata dictionary.

    Example:
        >>> result = SkillResult(
        ...     result_id="result1",
        ...     status=SkillResultStatus.SUCCESS,
        ...     output={"result": "Task completed"},
        ... )
        >>> result.status
        <SkillResultStatus.SUCCESS: 'success'>
    """

    result_id: str
    status: SkillResultStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate SkillResult attributes."""
        if not self.result_id:
            raise ValueError("result_id cannot be empty")

        if self.status == SkillResultStatus.SUCCESS and self.output is None:
            raise ValueError("SUCCESS status requires output")

        if self.status == SkillResultStatus.FAILURE and self.error is None:
            raise ValueError("FAILURE status requires error")
