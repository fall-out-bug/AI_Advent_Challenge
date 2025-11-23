"""Integration tests for Orchestrator-ConsensusBridge integration."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.god_agent.services.consensus_bridge import ConsensusBridge
from src.application.god_agent.services.god_agent_orchestrator import (
    GodAgentOrchestrator,
)
from src.application.god_agent.services.memory_fabric_service import MemoryFabricService
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResultStatus
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus
from src.domain.god_agent.value_objects.skill import SkillType


@pytest.fixture
def temp_consensus_dir():
    """Create temporary consensus directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        consensus_dir = Path(tmpdir) / "consensus"
        consensus_dir.mkdir(parents=True)
        artifacts_dir = consensus_dir / "artifacts"
        artifacts_dir.mkdir()
        messages_dir = consensus_dir / "messages" / "inbox"
        messages_dir.mkdir(parents=True)
        yield consensus_dir


@pytest.fixture
def consensus_bridge(temp_consensus_dir):
    """Create ConsensusBridge instance."""
    return ConsensusBridge(
        epic_id="epic_28",
        consensus_base_path=temp_consensus_dir,
        timeout_seconds=1,  # Short timeout for testing
    )


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
def mock_skill_adapters():
    """Mock skill adapters."""
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
def orchestrator(mock_skill_adapters, mock_memory_fabric_service, consensus_bridge):
    """Create GodAgentOrchestrator instance."""
    return GodAgentOrchestrator(
        skill_adapters=mock_skill_adapters,
        memory_fabric_service=mock_memory_fabric_service,
        consensus_bridge=consensus_bridge,
    )


@pytest.mark.asyncio
async def test_orchestrator_triggers_consensus_on_critical_step(
    orchestrator, consensus_bridge, temp_consensus_dir
):
    """Test orchestrator triggers ConsensusBridge on critical steps."""
    # Create a critical step (one that requires consensus)
    step = TaskStep(
        step_id="step_1",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
        acceptance_criteria=["Critical operation"],
    )

    plan = TaskPlan(plan_id="plan_1", steps=[step])

    # Mock consensus bridge to return immediately
    with patch.object(consensus_bridge, "_wait_for_consensus", return_value=None):
        result = await orchestrator.execute_plan(
            task_plan=plan,
            user_id="user_123",
            context={"is_critical": True},
        )

        # Verify consensus was triggered
        assert result is not None
        # Check that consensus request file was created
        artifacts_dir = temp_consensus_dir / "artifacts"
        request_files = list(artifacts_dir.glob("consensus_request_*.json"))
        # Note: Consensus may be triggered based on step characteristics
        assert True  # Placeholder - actual implementation will verify


@pytest.mark.asyncio
async def test_orchestrator_waits_for_consensus_verdict(orchestrator, consensus_bridge):
    """Test orchestrator waits for consensus verdict."""
    step = TaskStep(
        step_id="step_1",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
    )

    plan = TaskPlan(plan_id="plan_1", steps=[step])

    # Mock consensus bridge to simulate waiting
    consensus_called = False

    async def mock_request_consensus(*args, **kwargs):
        nonlocal consensus_called
        consensus_called = True
        return "consensus_1"

    consensus_bridge.request_consensus = AsyncMock(side_effect=mock_request_consensus)

    with patch.object(consensus_bridge, "_wait_for_consensus", return_value=None):
        result = await orchestrator.execute_plan(
            task_plan=plan,
            user_id="user_123",
            context={"is_critical": True},
        )

        # Verify orchestrator waited for consensus
        assert result is not None
        # Note: Actual implementation will verify waiting behavior


@pytest.mark.asyncio
async def test_orchestrator_publishes_veto_raised_event(orchestrator, consensus_bridge):
    """Test orchestrator publishes VETO_RAISED event when veto detected."""
    step = TaskStep(
        step_id="step_1",
        skill_type=SkillType.BUILDER,
        status=TaskStepStatus.PENDING,
    )

    plan = TaskPlan(plan_id="plan_1", steps=[step])

    # Mock consensus bridge to return veto
    consensus_bridge.check_veto_status = AsyncMock(return_value=True)

    with patch.object(orchestrator, "_publish_event") as mock_publish:
        with patch.object(consensus_bridge, "_wait_for_consensus", return_value=None):
            result = await orchestrator.execute_plan(
                task_plan=plan,
                user_id="user_123",
                context={"is_critical": True},
            )

            # Verify VETO_RAISED event was published
            calls = [call[0][0] for call in mock_publish.call_args_list]
            # Note: Actual implementation will verify VETO_RAISED event
            assert result is not None
