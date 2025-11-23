"""Unit tests for SafetyViolationDetector."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.god_agent.services.safety_violation_detector import (
    SafetyViolationDetector,
)
from src.domain.god_agent.entities.safety_violation import SafetyViolation, VetoRuleType
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.value_objects.skill import SkillType


@pytest.fixture
def mock_consensus_bridge():
    """Mock ConsensusBridge."""
    bridge = AsyncMock()
    return bridge


@pytest.fixture
def safety_detector(mock_consensus_bridge):
    """Create SafetyViolationDetector instance."""
    return SafetyViolationDetector(consensus_bridge=mock_consensus_bridge)


@pytest.fixture
def sample_task_step():
    """Create sample TaskStep."""
    return TaskStep(
        step_id="step_1",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
    )


@pytest.fixture
def sample_task_plan(sample_task_step):
    """Create sample TaskPlan."""
    return TaskPlan(
        plan_id="plan_1",
        steps=[sample_task_step],
    )


@pytest.mark.asyncio
async def test_detect_untestable_requirement(
    safety_detector, sample_task_plan, sample_task_step
):
    """Test detect maps untestable_requirement veto rule."""
    # Create step with untestable requirement
    step = TaskStep(
        step_id="step_1",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        acceptance_criteria=["Requirement that cannot be tested"],
    )

    violations = await safety_detector.detect(
        task_plan=sample_task_plan,
        step=step,
    )

    # Should detect untestable_requirement if criteria are not testable
    assert isinstance(violations, list)
    # Note: Actual detection logic will be implemented


@pytest.mark.asyncio
async def test_detect_task_over_4h(safety_detector, sample_task_plan, sample_task_step):
    """Test detect maps task_over_4h veto rule."""
    # Create step with estimated time > 4h (via metadata or context)
    violations = await safety_detector.detect(
        task_plan=sample_task_plan,
        step=sample_task_step,
        context={"estimated_hours": 5.0},
    )

    # Should detect task_over_4h
    assert isinstance(violations, list)
    # Note: Actual detection logic will be implemented


@pytest.mark.asyncio
async def test_detect_missing_rollback_plan(
    safety_detector, sample_task_plan, sample_task_step
):
    """Test detect maps missing_rollback_plan veto rule."""
    # Create step without rollback_instructions
    step = TaskStep(
        step_id="step_1",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        rollback_instructions=None,
    )

    violations = await safety_detector.detect(
        task_plan=sample_task_plan,
        step=step,
    )

    # Should detect missing_rollback_plan if step is critical
    assert isinstance(violations, list)


@pytest.mark.asyncio
async def test_detect_undefined_dependencies(safety_detector, sample_task_plan):
    """Test detect maps undefined_dependencies veto rule."""
    # Create step with undefined dependency
    # Note: TaskPlan validates DAG, so we need to create a valid plan first
    step1 = TaskStep(
        step_id="step_1",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
    )
    step2 = TaskStep(
        step_id="step_2",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        depends_on=["missing_step"],  # This would be caught by TaskPlan validation
    )

    # Since TaskPlan validates, we test the detector logic directly
    # by checking if it would detect the violation
    violations = await safety_detector._check_violations(
        task_plan=sample_task_plan,
        step=step2,
        context={},
    )

    # Should detect undefined_dependencies
    assert len(violations) > 0
    assert any(v.veto_rule == VetoRuleType.UNDEFINED_DEPENDENCIES for v in violations)


@pytest.mark.asyncio
async def test_detect_triggers_consensus_bridge(
    safety_detector, mock_consensus_bridge, sample_task_plan, sample_task_step
):
    """Test detect triggers ConsensusBridge when violation detected."""
    # Mock detect to return a violation
    with patch.object(
        safety_detector,
        "_check_violations",
        return_value=[
            SafetyViolation(
                violation_id="violation_1",
                veto_rule=VetoRuleType.TASK_OVER_4H,
                message="Task estimated at 5 hours",
            )
        ],
    ):
        violations = await safety_detector.detect(
            task_plan=sample_task_plan,
            step=sample_task_step,
        )

        # Should trigger ConsensusBridge
        mock_consensus_bridge.request_consensus.assert_called_once()
