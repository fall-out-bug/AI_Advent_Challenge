"""TaskStep domain entity."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from src.domain.god_agent.value_objects.skill import SkillType


class TaskStepStatus(str, Enum):
    """Task step status enumeration.

    Purpose:
        Represents the lifecycle state of a task step.

    Values:
        PENDING: Step created but not started
        RUNNING: Step currently executing
        SUCCEEDED: Step completed successfully
        FAILED: Step failed with error
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class TaskStep:
    """Task step domain entity.

    Purpose:
        Represents a single step in a task plan with skill assignment,
        status, dependencies, and acceptance gates.

    Attributes:
        step_id: Unique identifier for the step.
        skill_type: Type of skill to execute (concierge, research, etc.).
        status: Current status of the step.
        depends_on: List of step IDs this step depends on.
        acceptance_criteria: List of criteria that must be met for success.
        rollback_instructions: Optional instructions for rolling back.

    Example:
        >>> step = TaskStep(
        ...     step_id="step1",
        ...     skill_type=SkillType.RESEARCH,
        ...     status=TaskStepStatus.PENDING,
        ...     depends_on=[],
        ... )
        >>> step.step_id
        'step1'
    """

    step_id: str
    skill_type: SkillType
    status: TaskStepStatus
    depends_on: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    rollback_instructions: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate TaskStep attributes."""
        if not self.step_id:
            raise ValueError("step_id cannot be empty")
