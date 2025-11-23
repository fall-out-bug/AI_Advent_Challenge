"""Unit tests for TaskPlan entity."""

import pytest

from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.value_objects.skill import Skill, SkillContract, SkillType


def test_task_plan_creation():
    """Test TaskPlan creation with valid steps."""
    step1 = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
    )
    step2 = TaskStep(
        step_id="step2",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        depends_on=["step1"],
    )
    plan = TaskPlan(
        plan_id="plan1",
        steps=[step1, step2],
    )

    assert plan.plan_id == "plan1"
    assert len(plan.steps) == 2
    assert plan.steps[0].step_id == "step1"
    assert plan.steps[1].step_id == "step2"


def test_task_plan_max_depth_validation():
    """Test TaskPlan max depth validation - max 10 steps."""
    steps = [
        TaskStep(
            step_id=f"step{i}",
            skill_type=SkillType.CONCIERGE,
            status=TaskStepStatus.PENDING,
        )
        for i in range(10)
    ]
    plan = TaskPlan(plan_id="plan1", steps=steps)
    assert len(plan.steps) == 10

    # 11 steps should raise error
    steps.append(
        TaskStep(
            step_id="step11",
            skill_type=SkillType.CONCIERGE,
            status=TaskStepStatus.PENDING,
        )
    )
    with pytest.raises(ValueError, match="TaskPlan cannot have more than 10 steps"):
        TaskPlan(plan_id="plan1", steps=steps)


def test_task_plan_dag_validation_cycle():
    """Test TaskPlan DAG validation - detects cycles."""
    step1 = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
        depends_on=["step2"],
    )
    step2 = TaskStep(
        step_id="step2",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        depends_on=["step1"],
    )
    with pytest.raises(ValueError, match="TaskPlan contains cycle"):
        TaskPlan(plan_id="plan1", steps=[step1, step2])


def test_task_plan_dag_validation_missing_dependency():
    """Test TaskPlan DAG validation - missing dependency."""
    step1 = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
        depends_on=["step3"],  # step3 doesn't exist
    )
    with pytest.raises(ValueError, match="depends on missing step"):
        TaskPlan(plan_id="plan1", steps=[step1])


def test_task_plan_valid_dag():
    """Test TaskPlan with valid DAG."""
    step1 = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
    )
    step2 = TaskStep(
        step_id="step2",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        depends_on=["step1"],
    )
    step3 = TaskStep(
        step_id="step3",
        skill_type=SkillType.REVIEWER,
        status=TaskStepStatus.PENDING,
        depends_on=["step2"],
    )
    plan = TaskPlan(plan_id="plan1", steps=[step1, step2, step3])
    assert len(plan.steps) == 3
