"""Unit tests for ConsensusBridge."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.god_agent.services.consensus_bridge import ConsensusBridge
from src.domain.god_agent.entities.task_plan import TaskPlan
from src.domain.god_agent.entities.task_step import TaskStep, TaskStepStatus


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
        timeout_seconds=300,
    )


@pytest.fixture
def sample_task_step():
    """Create sample TaskStep."""
    from src.domain.god_agent.value_objects.skill import SkillType

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
async def test_request_consensus_creates_files(
    consensus_bridge, sample_task_plan, sample_task_step, temp_consensus_dir
):
    """Test request_consensus creates files following consensus_architecture.json schema."""
    # Mock _wait_for_consensus to return immediately
    with patch.object(consensus_bridge, "_wait_for_consensus", return_value=None):
        consensus_id = await consensus_bridge.request_consensus(
            task_plan=sample_task_plan,
            step=sample_task_step,
            context={"reason": "critical_step"},
        )

        assert consensus_id is not None

        # Check that files were created
        artifacts_dir = temp_consensus_dir / "artifacts"
        assert artifacts_dir.exists()

        # Check decision_log.jsonl exists
        decision_log = temp_consensus_dir / "decision_log.jsonl"
        assert decision_log.exists()

        # Check that decision log entry was created
        with open(decision_log, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0
            entry = json.loads(lines[-1])
            assert entry["epic_id"] == "epic_28"
            assert entry["decision"] in ["propose", "approve", "veto"]


@pytest.mark.asyncio
async def test_check_veto_status_reads_decision_log(
    consensus_bridge, temp_consensus_dir
):
    """Test check_veto_status reads decision_log.jsonl."""
    decision_log = temp_consensus_dir / "decision_log.jsonl"

    # Create a decision log entry with veto
    with open(decision_log, "w") as f:
        entry = {
            "timestamp": "2025_01_27_18_00_00",
            "agent": "quality",
            "decision": "veto",
            "epic_id": "epic_28",
            "iteration": 1,
            "previous_artifacts": ["plan.json"],
            "details": {
                "status": "review.json emitted with VETO verdict",
                "veto_triggers": ["untestable_requirement"],
            },
        }
        f.write(json.dumps(entry) + "\n")

    has_veto = await consensus_bridge.check_veto_status("consensus_1")

    assert has_veto is True


@pytest.mark.asyncio
async def test_check_veto_status_returns_false_when_no_veto(
    consensus_bridge, temp_consensus_dir
):
    """Test check_veto_status returns False when no veto."""
    decision_log = temp_consensus_dir / "decision_log.jsonl"

    # Create a decision log entry with approve
    with open(decision_log, "w") as f:
        entry = {
            "timestamp": "2025_01_27_18_00_00",
            "agent": "quality",
            "decision": "approve",
            "epic_id": "epic_28",
            "iteration": 1,
            "previous_artifacts": ["plan.json"],
            "details": {"status": "review.json emitted with APPROVE verdict"},
        }
        f.write(json.dumps(entry) + "\n")

    has_veto = await consensus_bridge.check_veto_status("consensus_1")

    assert has_veto is False


@pytest.mark.asyncio
async def test_request_consensus_timeout_after_5_minutes(
    consensus_bridge, sample_task_plan, sample_task_step
):
    """Test request_consensus times out after 5 minutes."""
    consensus_bridge.timeout_seconds = 0.1  # Set to 0.1 second for testing

    # Mock _wait_for_consensus to raise TimeoutError
    async def mock_wait(consensus_id: str):
        await asyncio.sleep(0.2)  # Sleep longer than timeout
        raise asyncio.TimeoutError("Timeout")

    with patch.object(consensus_bridge, "_wait_for_consensus", side_effect=mock_wait):
        with pytest.raises(asyncio.TimeoutError):
            await consensus_bridge.request_consensus(
                task_plan=sample_task_plan,
                step=sample_task_step,
                context={"reason": "critical_step"},
            )


@pytest.mark.asyncio
async def test_request_consensus_creates_message_files(
    consensus_bridge, sample_task_plan, sample_task_step, temp_consensus_dir
):
    """Test request_consensus creates message files in inbox directories."""
    # Mock _wait_for_consensus to return immediately
    with patch.object(consensus_bridge, "_wait_for_consensus", return_value=None):
        consensus_id = await consensus_bridge.request_consensus(
            task_plan=sample_task_plan,
            step=sample_task_step,
            context={"reason": "critical_step"},
        )

        assert consensus_id is not None

        # Check that consensus request file was created
        artifacts_dir = temp_consensus_dir / "artifacts"
        request_files = list(artifacts_dir.glob("consensus_request_*.json"))
        assert len(request_files) > 0
