"""TaskPlan domain entity."""

from dataclasses import dataclass, field
from typing import List

from src.domain.god_agent.entities.task_step import TaskStep

MAX_PLAN_DEPTH = 10


@dataclass
class TaskPlan:
    """Task plan domain entity.

    Purpose:
        Represents a multi-step task plan as a DAG with dependencies,
        acceptance criteria, and rollback instructions.

    Attributes:
        plan_id: Unique identifier for the plan.
        steps: List of task steps in the plan.
        max_depth: Maximum number of steps allowed (default: 10).

    Example:
        >>> step1 = TaskStep(
        ...     step_id="step1",
        ...     skill_type=SkillType.RESEARCH,
        ...     status=TaskStepStatus.PENDING,
        ... )
        >>> plan = TaskPlan(plan_id="plan1", steps=[step1])
        >>> plan.plan_id
        'plan1'
    """

    plan_id: str
    steps: List[TaskStep] = field(default_factory=list)
    max_depth: int = MAX_PLAN_DEPTH

    def __post_init__(self) -> None:
        """Validate TaskPlan attributes."""
        if not self.plan_id:
            raise ValueError("plan_id cannot be empty")

        if len(self.steps) > self.max_depth:
            raise ValueError(f"TaskPlan cannot have more than {self.max_depth} steps")

        self._validate_dag()

    def _validate_dag(self) -> None:
        """Validate that steps form a valid DAG (no cycles).

        Raises:
            ValueError: If DAG contains cycles or missing dependencies.
        """
        step_ids = {step.step_id for step in self.steps}

        # Check for missing dependencies
        for step in self.steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    raise ValueError(
                        f"TaskPlan step {step.step_id} depends on missing step {dep_id}"
                    )

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(step_id: str) -> bool:
            if step_id in rec_stack:
                return True
            if step_id in visited:
                return False

            visited.add(step_id)
            rec_stack.add(step_id)

            step = next((s for s in self.steps if s.step_id == step_id), None)
            if step:
                for dep_id in step.depends_on:
                    if has_cycle(dep_id):
                        return True

            rec_stack.remove(step_id)
            return False

        for step in self.steps:
            if has_cycle(step.step_id):
                raise ValueError("TaskPlan contains cycle")
