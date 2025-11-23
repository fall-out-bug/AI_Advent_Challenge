"""Performance tests for multi-step flows."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.god_agent.services.god_agent_orchestrator import (
    GodAgentOrchestrator,
)
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.value_objects.skill import SkillType


@pytest.mark.asyncio
async def test_multi_step_flows_performance():
    """Test multi-step flows performance < 30s."""
    # Setup
    mock_memory_fabric = AsyncMock()
    mock_consensus_bridge = AsyncMock()
    mock_safety_detector = AsyncMock()
    mock_safety_detector.detect_violations.return_value = []

    orchestrator = GodAgentOrchestrator(
        memory_fabric_service=mock_memory_fabric,
        skill_adapters={},
        consensus_bridge=mock_consensus_bridge,
    )
    orchestrator.safety_violation_detector = mock_safety_detector

    # Create a simple multi-step plan
    task_plan = TaskPlan(
        plan_id="plan_1",
        steps=[
            TaskStep(
                step_id="step_1",
                skill_type=SkillType.CONCIERGE,
                status=TaskStepStatus.PENDING,
            ),
            TaskStep(
                step_id="step_2",
                skill_type=SkillType.RESEARCH,
                status=TaskStepStatus.PENDING,
                depends_on=["step_1"],
            ),
        ],
    )

    # Mock skill adapter
    from src.domain.god_agent.entities.skill_result import (
        SkillResult,
        SkillResultStatus,
    )

    mock_adapter = AsyncMock()
    mock_adapter.execute.return_value = SkillResult(
        result_id="result_1",
        status=SkillResultStatus.SUCCESS,
        output={"reply": "Done"},
    )
    orchestrator.skill_adapters[SkillType.CONCIERGE] = mock_adapter
    orchestrator.skill_adapters[SkillType.RESEARCH] = mock_adapter

    # Measure
    start_time = time.perf_counter()
    result = await orchestrator.execute_plan(task_plan, "123")
    duration = time.perf_counter() - start_time

    # Assert
    assert duration < 30.0, f"Multi-step flow took {duration}s, expected < 30s"
    assert result is not None
