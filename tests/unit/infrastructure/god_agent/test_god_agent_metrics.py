"""Unit tests for GodAgentMetrics."""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.god_agent.metrics import (
    GodAgentMetrics,
    record_plan_duration,
    record_skill_latency,
    record_task_execution,
    record_veto,
)


@pytest.fixture
def metrics():
    """Create GodAgentMetrics instance."""
    return GodAgentMetrics()


@pytest.mark.asyncio
async def test_record_task_execution_increments_counter(metrics):
    """Test record_task_execution increments god_agent_tasks_total."""
    with patch.object(
        metrics.tasks_total.labels("concierge", "success"), "inc"
    ) as mock_inc:
        record_task_execution("concierge", "success")
        mock_inc.assert_called_once()


@pytest.mark.asyncio
async def test_record_plan_duration_observes_histogram(metrics):
    """Test record_plan_duration observes god_agent_plan_duration_seconds."""
    with patch.object(metrics.plan_duration_seconds, "observe") as mock_observe:
        record_plan_duration(2.5)
        mock_observe.assert_called_once_with(2.5)


@pytest.mark.asyncio
async def test_record_veto_increments_counter(metrics):
    """Test record_veto increments god_agent_veto_total."""
    with patch.object(
        metrics.veto_total.labels("untestable_requirement"), "inc"
    ) as mock_inc:
        record_veto("untestable_requirement")
        mock_inc.assert_called_once()


@pytest.mark.asyncio
async def test_record_skill_latency_observes_histogram(metrics):
    """Test record_skill_latency observes god_agent_skill_latency_seconds."""
    with patch.object(
        metrics.skill_latency_seconds.labels("concierge"), "observe"
    ) as mock_observe:
        record_skill_latency("concierge", 0.5)
        mock_observe.assert_called_once_with(0.5)


@pytest.mark.asyncio
async def test_metrics_registration():
    """Test all metrics are registered."""
    metrics = GodAgentMetrics()

    assert metrics.tasks_total is not None
    assert metrics.plan_duration_seconds is not None
    assert metrics.veto_total is not None
    assert metrics.skill_latency_seconds is not None
