"""Smoke tests for God Agent end-to-end flows."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.god_agent.services.god_agent_orchestrator import (
    GodAgentOrchestrator,
)
from src.domain.god_agent.entities.skill_result import SkillResult, SkillResultStatus
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.value_objects.skill import SkillType


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator with all skill adapters."""
    mock_memory_fabric = AsyncMock()
    mock_consensus_bridge = AsyncMock()
    mock_consensus_bridge.check_veto_status.return_value = False

    orchestrator = GodAgentOrchestrator(
        skill_adapters={},
        memory_fabric_service=mock_memory_fabric,
        consensus_bridge=mock_consensus_bridge,
    )

    # Mock all skill adapters
    for skill_type in SkillType:
        mock_adapter = AsyncMock()
        mock_adapter.execute.return_value = SkillResult(
            result_id=f"result_{skill_type.value}",
            status=SkillResultStatus.SUCCESS,
            output={"reply": f"Success from {skill_type.value}"},
        )
        orchestrator.skill_adapters[skill_type] = mock_adapter

    return orchestrator


@pytest.mark.asyncio
async def test_concierge_smoke_flow(mock_orchestrator):
    """Smoke test for concierge skill flow."""
    task_plan = TaskPlan(
        plan_id="concierge_plan",
        steps=[
            TaskStep(
                step_id="step_1",
                skill_type=SkillType.CONCIERGE,
                status=TaskStepStatus.PENDING,
            ),
        ],
    )

    result = await mock_orchestrator.execute_plan(task_plan, "user_123")

    assert result["status"] == "completed"
    assert len(result["step_results"]) == 1
    assert result["step_results"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_research_smoke_flow(mock_orchestrator):
    """Smoke test for research skill flow."""
    task_plan = TaskPlan(
        plan_id="research_plan",
        steps=[
            TaskStep(
                step_id="step_1",
                skill_type=SkillType.RESEARCH,
                status=TaskStepStatus.PENDING,
            ),
        ],
    )

    result = await mock_orchestrator.execute_plan(task_plan, "user_123")

    assert result["status"] == "completed"
    assert len(result["step_results"]) == 1
    assert result["step_results"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_builder_smoke_flow(mock_orchestrator):
    """Smoke test for builder skill flow."""
    task_plan = TaskPlan(
        plan_id="builder_plan",
        steps=[
            TaskStep(
                step_id="step_1",
                skill_type=SkillType.BUILDER,
                status=TaskStepStatus.PENDING,
            ),
        ],
    )

    result = await mock_orchestrator.execute_plan(task_plan, "user_123")

    assert result["status"] == "completed"
    assert len(result["step_results"]) == 1
    assert result["step_results"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_reviewer_smoke_flow(mock_orchestrator):
    """Smoke test for reviewer skill flow."""
    task_plan = TaskPlan(
        plan_id="reviewer_plan",
        steps=[
            TaskStep(
                step_id="step_1",
                skill_type=SkillType.REVIEWER,
                status=TaskStepStatus.PENDING,
            ),
        ],
    )

    result = await mock_orchestrator.execute_plan(task_plan, "user_123")

    assert result["status"] == "completed"
    assert len(result["step_results"]) == 1
    assert result["step_results"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_ops_smoke_flow(mock_orchestrator):
    """Smoke test for ops skill flow."""
    task_plan = TaskPlan(
        plan_id="ops_plan",
        steps=[
            TaskStep(
                step_id="step_1",
                skill_type=SkillType.OPS,
                status=TaskStepStatus.PENDING,
            ),
        ],
    )

    result = await mock_orchestrator.execute_plan(task_plan, "user_123")

    assert result["status"] == "completed"
    assert len(result["step_results"]) == 1
    assert result["step_results"][0]["status"] == "success"
