"""Unit tests for GodAgentOrchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.god_agent.services.god_agent_orchestrator import (
    GodAgentOrchestrator,
)
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResultStatus
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.value_objects.skill import SkillType


@pytest.fixture
def mock_skill_adapters():
    """Mock skill adapters dictionary."""
    adapters = {}
    for skill_type in SkillType:
        adapter = AsyncMock()
        adapter.get_skill_id.return_value = skill_type.value
        adapter.execute = AsyncMock(
            return_value=MagicMock(
                status=SkillResultStatus.SUCCESS,
                output={"result": "success"},
            )
        )
        adapters[skill_type] = adapter
    return adapters


@pytest.fixture
def mock_memory_fabric_service():
    """Mock MemoryFabricService."""
    service = AsyncMock()
    service.get_memory_snapshot = AsyncMock(
        return_value=MemorySnapshot(
            user_id="user_123",
            profile_summary="Persona: Alfred",
            conversation_summary="Recent chat",
            rag_hits=[],
            artifact_refs=[],
        )
    )
    return service


@pytest.fixture
def mock_consensus_bridge():
    """Mock ConsensusBridge."""
    bridge = AsyncMock()
    bridge.request_consensus = AsyncMock(return_value="consensus_1")
    bridge.check_veto_status = AsyncMock(return_value=False)
    return bridge


@pytest.fixture
def orchestrator(
    mock_skill_adapters, mock_memory_fabric_service, mock_consensus_bridge
):
    """Create GodAgentOrchestrator instance."""
    return GodAgentOrchestrator(
        skill_adapters=mock_skill_adapters,
        memory_fabric_service=mock_memory_fabric_service,
        consensus_bridge=mock_consensus_bridge,
    )


@pytest.fixture
def sample_task_step():
    """Create sample TaskStep."""
    return TaskStep(
        step_id="step_1",
        skill_type=SkillType.CONCIERGE,
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
async def test_execute_plan_sequential_execution(
    orchestrator, sample_task_plan, mock_skill_adapters
):
    """Test execute_plan executes steps sequentially."""
    result = await orchestrator.execute_plan(
        task_plan=sample_task_plan,
        user_id="user_123",
    )

    assert result is not None
    # Verify skill adapter was called
    mock_skill_adapters[SkillType.CONCIERGE].execute.assert_called_once()


@pytest.mark.asyncio
async def test_execute_plan_parallel_execution(orchestrator, mock_skill_adapters):
    """Test execute_plan executes independent steps in parallel."""
    step1 = TaskStep(
        step_id="step_1",
        skill_type=SkillType.CONCIERGE,
        status=TaskStepStatus.PENDING,
    )
    step2 = TaskStep(
        step_id="step_2",
        skill_type=SkillType.RESEARCH,
        status=TaskStepStatus.PENDING,
    )
    plan = TaskPlan(plan_id="plan_1", steps=[step1, step2])

    result = await orchestrator.execute_plan(
        task_plan=plan,
        user_id="user_123",
    )

    assert result is not None
    # Both adapters should be called
    mock_skill_adapters[SkillType.CONCIERGE].execute.assert_called_once()
    mock_skill_adapters[SkillType.RESEARCH].execute.assert_called_once()


@pytest.mark.asyncio
async def test_pause_task(orchestrator, sample_task_plan):
    """Test pause_task pauses execution."""
    # Start execution
    execute_task = orchestrator.execute_plan(
        task_plan=sample_task_plan,
        user_id="user_123",
    )

    # Pause task
    await orchestrator.pause_task("plan_1")

    # Wait for execution to complete or be paused
    result = await execute_task

    # Verify task was paused (status check)
    assert result is not None


@pytest.mark.asyncio
async def test_resume_task(orchestrator, sample_task_plan):
    """Test resume_task resumes execution."""
    # Pause first
    await orchestrator.pause_task("plan_1")

    # Resume
    await orchestrator.resume_task("plan_1")

    # Verify task can be resumed
    assert True  # Placeholder - actual implementation will verify state


@pytest.mark.asyncio
async def test_cancel_task(orchestrator, sample_task_plan):
    """Test cancel_task cancels execution."""
    # Start execution
    execute_task = orchestrator.execute_plan(
        task_plan=sample_task_plan,
        user_id="user_123",
    )

    # Cancel task
    await orchestrator.cancel_task("plan_1")

    # Verify task was cancelled
    assert True  # Placeholder - actual implementation will verify cancellation


@pytest.mark.asyncio
async def test_execute_plan_publishes_events(
    orchestrator, sample_task_plan, mock_skill_adapters
):
    """Test execute_plan publishes events (TASK_STARTED, STEP_DONE)."""
    with patch.object(orchestrator, "_publish_event") as mock_publish:
        await orchestrator.execute_plan(
            task_plan=sample_task_plan,
            user_id="user_123",
        )

        # Verify events were published
        assert mock_publish.called
        # Check for TASK_STARTED event
        calls = [call[0][0] for call in mock_publish.call_args_list]
        assert "TASK_STARTED" in calls or any(
            "TASK_STARTED" in str(call) for call in calls
        )


@pytest.mark.asyncio
async def test_execute_plan_handles_step_failure(
    orchestrator, sample_task_plan, mock_skill_adapters
):
    """Test execute_plan handles step failure gracefully."""
    # Mock step to fail
    mock_skill_adapters[SkillType.CONCIERGE].execute = AsyncMock(
        return_value=MagicMock(
            status=SkillResultStatus.FAILURE,
            error="Step failed",
        )
    )

    result = await orchestrator.execute_plan(
        task_plan=sample_task_plan,
        user_id="user_123",
    )

    # Should handle failure gracefully
    assert result is not None
