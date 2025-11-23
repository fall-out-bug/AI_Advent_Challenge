"""Unit tests for TaskStep entity."""

import pytest

from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.value_objects.skill import SkillType


def test_task_step_creation():
    """Test TaskStep creation."""
    step = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
    )

    assert step.step_id == "step1"
    assert step.skill_type == SkillType.RESEARCH
    assert step.status == TaskStepStatus.PENDING
    assert step.depends_on == []


def test_task_step_status_transitions():
    """Test TaskStep status transitions."""
    step = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
    )

    # PENDING -> RUNNING
    step.status = TaskStepStatus.RUNNING
    assert step.status == TaskStepStatus.RUNNING

    # RUNNING -> SUCCEEDED
    step.status = TaskStepStatus.SUCCEEDED
    assert step.status == TaskStepStatus.SUCCEEDED

    # RUNNING -> FAILED
    step.status = TaskStepStatus.RUNNING
    step.status = TaskStepStatus.FAILED
    assert step.status == TaskStepStatus.FAILED


def test_task_step_acceptance_gates():
    """Test TaskStep acceptance gates."""
    step = TaskStep(
        step_id="step1",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
        acceptance_criteria=["result contains citations", "response time < 5s"],
    )

    assert len(step.acceptance_criteria) == 2
    assert "result contains citations" in step.acceptance_criteria


def test_task_step_dependencies():
    """Test TaskStep dependencies."""
    step = TaskStep(
        step_id="step2",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        depends_on=["step1"],
    )

    assert step.depends_on == ["step1"]
    assert len(step.depends_on) == 1
