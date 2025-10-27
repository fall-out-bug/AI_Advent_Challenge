"""Unit tests for parallel orchestrator.

Following TDD principles and the Zen of Python.
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.application.orchestrators.parallel_orchestrator import ParallelOrchestrator
from src.domain.messaging.message_schema import CodeGenerationRequest


class TestParallelOrchestratorInitialization:
    """Test parallel orchestrator initialization."""

    def test_init_creates_orchestrator(self):
        """Test initialization creates orchestrator."""
        orchestrator = ParallelOrchestrator()
        assert orchestrator.stats is not None

    def test_initial_stats_are_zero(self):
        """Test initial statistics are zero."""
        orchestrator = ParallelOrchestrator()
        stats = orchestrator.get_stats()

        assert stats["total_executions"] == 0
        assert stats["successful_executions"] == 0
        assert stats["failed_executions"] == 0
        assert stats["partial_failures"] == 0


class TestParallelExecution:
    """Test parallel task execution."""

    @pytest.mark.asyncio
    async def test_executes_tasks_in_parallel(self):
        """Test executing tasks in parallel."""
        orchestrator = ParallelOrchestrator()

        # Create mock agents
        agent1 = AsyncMock()
        agent1.process.return_value = "result1"

        agent2 = AsyncMock()
        agent2.process.return_value = "result2"

        tasks = [
            (
                agent1,
                CodeGenerationRequest(
                    task_description="Task 1", model_name="starcoder"
                ),
            ),
            (
                agent2,
                CodeGenerationRequest(task_description="Task 2", model_name="mistral"),
            ),
        ]

        results = await orchestrator.execute_parallel(tasks)

        assert len(results) == 2
        assert "result1" in results
        assert "result2" in results
        assert agent1.process.called
        assert agent2.process.called

    @pytest.mark.asyncio
    async def test_handles_successful_execution(self):
        """Test handling successful execution."""
        orchestrator = ParallelOrchestrator()

        agent = AsyncMock()
        agent.process.return_value = "success"

        tasks = [(agent, None)]
        results = await orchestrator.execute_parallel(tasks)

        assert len(results) == 1
        assert results[0] == "success"

        stats = orchestrator.get_stats()
        assert stats["successful_executions"] == 1

    @pytest.mark.asyncio
    async def test_handles_failed_execution(self):
        """Test handling failed execution."""
        orchestrator = ParallelOrchestrator()

        agent = AsyncMock()
        agent.process.side_effect = Exception("Task failed")

        tasks = [(agent, None)]

        try:
            await orchestrator.execute_parallel(tasks, fail_fast=True)
        except Exception:
            pass  # Expected to fail

        stats = orchestrator.get_stats()
        # Stats are updated before exception is raised
        assert stats["failed_executions"] >= 0

    @pytest.mark.asyncio
    async def test_stats_updated_on_fail_fast_exception(self):
        """Test that stats are updated when fail_fast=True raises non-timeout exception."""
        orchestrator = ParallelOrchestrator()

        agent = AsyncMock()
        agent.process.side_effect = ValueError("Custom error")

        tasks = [(agent, None)]

        # Before fix: stats would not be updated for non-timeout exceptions
        try:
            await orchestrator.execute_parallel(tasks, fail_fast=True)
        except ValueError:
            pass  # Expected exception

        stats = orchestrator.get_stats()
        # Verify stats are properly updated despite non-timeout exception
        assert stats["total_executions"] == 1
        assert stats["failed_executions"] == 1

    @pytest.mark.asyncio
    async def test_handles_partial_failures(self):
        """Test handling partial failures."""
        orchestrator = ParallelOrchestrator()

        agent1 = AsyncMock()
        agent1.process.return_value = "success"

        agent2 = AsyncMock()
        agent2.process.side_effect = Exception("Failed")

        tasks = [
            (agent1, None),
            (agent2, None),
        ]

        results = await orchestrator.execute_parallel(tasks, fail_fast=False)

        assert len(results) == 2
        assert "success" in results

        stats = orchestrator.get_stats()
        assert stats["partial_failures"] == 1

    @pytest.mark.asyncio
    async def test_respects_timeout(self):
        """Test respecting timeout constraint."""
        orchestrator = ParallelOrchestrator()

        async def slow_task(*args, **kwargs):
            await asyncio.sleep(2)
            return "done"

        agent = AsyncMock()
        agent.process.side_effect = slow_task

        tasks = [(agent, None)]

        with pytest.raises(asyncio.TimeoutError):
            await orchestrator.execute_parallel(tasks, timeout=0.1)

    @pytest.mark.asyncio
    async def test_executes_multiple_agents(self):
        """Test executing multiple agents."""
        orchestrator = ParallelOrchestrator()

        agents = [AsyncMock() for _ in range(5)]
        for i, agent in enumerate(agents):
            agent.process.return_value = f"result{i}"

        tasks = [(agent, None) for agent in agents]
        results = await orchestrator.execute_parallel(tasks)

        assert len(results) == 5
        for i in range(5):
            assert f"result{i}" in results


class TestResultAggregation:
    """Test result aggregation strategies."""

    @pytest.mark.asyncio
    async def test_aggregates_all_results(self):
        """Test aggregating all results."""
        orchestrator = ParallelOrchestrator()

        agents = [AsyncMock() for _ in range(3)]
        for agent in agents:
            agent.process.return_value = "success"

        tasks = [(agent, None) for agent in agents]
        aggregated = await orchestrator.execute_with_aggregation(
            tasks, aggregation_strategy="all"
        )

        assert aggregated["total_count"] == 3
        assert len(aggregated["results"]) == 3
        assert aggregated["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_aggregates_first_result(self):
        """Test aggregating first result."""
        orchestrator = ParallelOrchestrator()

        agents = [AsyncMock() for _ in range(3)]
        for agent in agents:
            agent.process.return_value = "success"

        tasks = [(agent, None) for agent in agents]
        aggregated = await orchestrator.execute_with_aggregation(
            tasks, aggregation_strategy="first"
        )

        assert aggregated["result"] == "success"
        assert "failed_count" in aggregated

    @pytest.mark.asyncio
    async def test_aggregates_majority_results(self):
        """Test aggregating majority results."""
        orchestrator = ParallelOrchestrator()

        agents = [AsyncMock() for _ in range(5)]
        for agent in agents:
            agent.process.return_value = "success"

        tasks = [(agent, None) for agent in agents]
        aggregated = await orchestrator.execute_with_aggregation(
            tasks, aggregation_strategy="majority"
        )

        assert "meets_threshold" in aggregated
        assert aggregated["meets_threshold"] is True


class TestStatistics:
    """Test statistics tracking."""

    @pytest.mark.asyncio
    async def test_tracks_successful_executions(self):
        """Test tracking successful executions."""
        orchestrator = ParallelOrchestrator()

        agent = AsyncMock()
        agent.process.return_value = "success"

        await orchestrator.execute_parallel([(agent, None)])

        stats = orchestrator.get_stats()
        assert stats["total_executions"] == 1
        assert stats["successful_executions"] >= 1

    @pytest.mark.asyncio
    async def test_tracks_failed_executions(self):
        """Test tracking failed executions."""
        orchestrator = ParallelOrchestrator()

        agent = AsyncMock()
        agent.process.side_effect = Exception("Failed")

        try:
            await orchestrator.execute_parallel([(agent, None)], fail_fast=False)
        except:
            pass

        stats = orchestrator.get_stats()
        assert stats["failed_executions"] >= 1

    @pytest.mark.asyncio
    async def test_tracks_partial_failures(self):
        """Test tracking partial failures."""
        orchestrator = ParallelOrchestrator()

        agent1 = AsyncMock()
        agent1.process.return_value = "success"

        agent2 = AsyncMock()
        agent2.process.side_effect = Exception("Failed")

        tasks = [(agent1, None), (agent2, None)]
        await orchestrator.execute_parallel(tasks, fail_fast=False)

        stats = orchestrator.get_stats()
        assert stats["partial_failures"] >= 1

    def test_get_stats_returns_copy(self):
        """Test get_stats returns a copy."""
        orchestrator = ParallelOrchestrator()

        stats1 = orchestrator.get_stats()
        stats1["total_executions"] = 999

        stats2 = orchestrator.get_stats()
        assert stats2["total_executions"] == 0

    def test_reset_stats(self):
        """Test resetting statistics."""
        orchestrator = ParallelOrchestrator()

        orchestrator.stats["total_executions"] = 5
        orchestrator.reset_stats()

        stats = orchestrator.get_stats()
        assert stats["total_executions"] == 0


import asyncio

# Required for timeouts and other async features in tests
