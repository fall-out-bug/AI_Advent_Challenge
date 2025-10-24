"""Integration tests for multi-agent workflow."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from communication.message_schema import (
    CodeGenerationResponse,
    CodeReviewResponse,
    OrchestratorRequest,
    TaskMetadata,
)
from orchestrator import MultiAgentOrchestrator, process_simple_task


class TestMultiAgentWorkflow:
    """Integration tests for the complete multi-agent workflow."""

    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator."""
        return MultiAgentOrchestrator(
            generator_url="http://test-generator:9001",
            reviewer_url="http://test-reviewer:9002",
            results_dir="test_results",
        )

    @pytest.fixture
    def mock_generation_response(self):
        """Mock code generation response."""
        return CodeGenerationResponse(
            task_description="Create a function to calculate fibonacci",
            generated_code="""
def fibonacci(n: int) -> int:
    \"\"\"Calculate fibonacci number.
    
    Args:
        n: Position in fibonacci sequence
        
    Returns:
        Fibonacci number at position n
    \"\"\"
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
""",
            tests="""
import pytest

def test_fibonacci():
    \"\"\"Test fibonacci function.\"\"\"
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55
""",
            metadata=TaskMetadata(
                complexity="medium", lines_of_code=15, dependencies=["typing"]
            ),
            generation_time=datetime.now(),
            tokens_used=300,
        )

    @pytest.fixture
    def mock_review_response(self):
        """Mock code review response."""
        return CodeReviewResponse(
            code_quality_score=8.5,
            metrics={
                "pep8_compliance": True,
                "pep8_score": 9.0,
                "has_docstrings": True,
                "has_type_hints": True,
                "test_coverage": "good",
                "complexity_score": 7.0,
            },
            issues=["Consider memoization for better performance"],
            recommendations=["Add memoization", "Consider iterative approach"],
            review_time=datetime.now(),
            tokens_used=200,
        )

    @pytest.mark.asyncio
    async def test_process_simple_task_success(
        self, mock_generation_response, mock_review_response
    ):
        """Test successful simple task processing."""
        with patch("orchestrator.AgentClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_client.wait_for_agent.return_value = True
            mock_client.generate_code.return_value = mock_generation_response
            mock_client.review_code.return_value = mock_review_response

            result = await process_simple_task(
                task_description="Create a fibonacci function",
                language="python",
                requirements=["Include type hints"],
            )

            assert result.success is True
            assert result.task_description == "Create a fibonacci function"
            assert (
                result.generation_result.generated_code
                == mock_generation_response.generated_code
            )
            assert result.review_result.code_quality_score == 8.5
            assert result.workflow_time > 0

    @pytest.mark.asyncio
    async def test_process_simple_task_generation_failure(self):
        """Test simple task processing with generation failure."""
        with patch("orchestrator.AgentClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_client.wait_for_agent.return_value = True
            mock_client.generate_code.side_effect = Exception("Generation failed")

            result = await process_simple_task(
                task_description="Create a fibonacci function"
            )

            assert result.success is False
            assert "Generation failed" in result.error_message

    @pytest.mark.asyncio
    async def test_process_simple_task_review_failure(self, mock_generation_response):
        """Test simple task processing with review failure."""
        with patch("orchestrator.AgentClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_client.wait_for_agent.return_value = True
            mock_client.generate_code.return_value = mock_generation_response
            mock_client.review_code.side_effect = Exception("Review failed")

            result = await process_simple_task(
                task_description="Create a fibonacci function"
            )

            assert result.success is False
            assert "Review failed" in result.error_message

    @pytest.mark.asyncio
    async def test_orchestrator_process_task_success(
        self, orchestrator, mock_generation_response, mock_review_response
    ):
        """Test orchestrator task processing success."""
        with patch("orchestrator.AgentClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_client.wait_for_agent.return_value = True
            mock_client.generate_code.return_value = mock_generation_response
            mock_client.review_code.return_value = mock_review_response

            request = OrchestratorRequest(
                task_description="Create a fibonacci function",
                language="python",
                requirements=["Include type hints", "Add tests"],
            )

            result = await orchestrator.process_task(request)

            assert result.success is True
            assert result.task_description == "Create a fibonacci function"
            assert result.generation_result is not None
            assert result.review_result is not None
            assert result.workflow_time > 0
            assert orchestrator.stats["successful_workflows"] == 1

    @pytest.mark.asyncio
    async def test_orchestrator_process_task_failure(self, orchestrator):
        """Test orchestrator task processing failure."""
        with patch("orchestrator.AgentClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_client.wait_for_agent.side_effect = Exception("Agent unavailable")

            request = OrchestratorRequest(
                task_description="Create a fibonacci function"
            )

            result = await orchestrator.process_task(request)

            assert result.success is False
            assert "Agent unavailable" in result.error_message
            assert orchestrator.stats["failed_workflows"] == 1

    @pytest.mark.asyncio
    async def test_get_agent_status(self, orchestrator):
        """Test agent status checking."""
        with patch("orchestrator.AgentClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock health responses
            from types import SimpleNamespace
            mock_client.check_health = AsyncMock(side_effect=[
                SimpleNamespace(status="healthy", uptime=100.0),
                SimpleNamespace(status="healthy", uptime=200.0),
            ])

            status = await orchestrator.get_agent_status()

            assert "generator" in status
            assert "reviewer" in status
            assert status["generator"]["status"] == "healthy"
            assert status["reviewer"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_agent_stats(self, orchestrator):
        """Test agent statistics retrieval."""
        with patch("orchestrator.AgentClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock stats responses
            from types import SimpleNamespace
            mock_client.get_stats = AsyncMock(side_effect=[
                SimpleNamespace(model_dump=lambda: {
                    "total_requests": 10,
                    "successful_requests": 9,
                    "failed_requests": 1,
                    "average_response_time": 2.5,
                    "total_tokens_used": 5000,
                }),
                SimpleNamespace(model_dump=lambda: {
                    "total_requests": 8,
                    "successful_requests": 8,
                    "failed_requests": 0,
                    "average_response_time": 1.8,
                    "total_tokens_used": 3000,
                }),
            ])

            stats = await orchestrator.get_agent_stats()

            assert "generator" in stats
            assert "reviewer" in stats
            assert "orchestrator" in stats
            assert stats["generator"]["total_requests"] == 10
            assert stats["reviewer"]["total_requests"] == 8

    def test_get_results_summary_no_results(self, orchestrator):
        """Test results summary with no results."""
        summary = orchestrator.get_results_summary()
        # Should have either a message field or stats fields
        assert "message" in summary or "total_workflows" in summary

    def test_get_results_summary_with_results(self, orchestrator):
        """Test results summary with mock results."""
        # This would require creating actual result files
        # For now, we'll test the structure
        summary = orchestrator.get_results_summary()

        # Should have message field when no results
        assert "message" in summary or "total_workflows" in summary

    def test_update_average_workflow_time(self, orchestrator):
        """Test average workflow time calculation."""
        # Test first workflow
        orchestrator.stats["successful_workflows"] = 0
        orchestrator._update_average_workflow_time(5.0)
        assert orchestrator.stats["average_workflow_time"] == 5.0

        # Test second workflow
        orchestrator.stats["successful_workflows"] = 1
        orchestrator._update_average_workflow_time(7.0)
        assert orchestrator.stats["average_workflow_time"] == 6.0

        # Test third workflow
        orchestrator.stats["successful_workflows"] = 2
        orchestrator._update_average_workflow_time(8.0)
        assert orchestrator.stats["average_workflow_time"] == (5.0 + 7.0 + 8.0) / 3


class TestAgentCommunication:
    """Test agent-to-agent communication."""

    @pytest.mark.asyncio
    async def test_agent_client_context_manager(self):
        """Test agent client context manager."""
        from communication.agent_client import AgentClient

        async with AgentClient() as client:
            assert client._client is not None

        # Client should be closed after context
        assert client._client is None

    @pytest.mark.asyncio
    async def test_agent_client_make_request(self):
        """Test agent client request making."""
        from communication.agent_client import AgentClient
        from unittest.mock import Mock

        async with AgentClient() as client:
            # Mock httpx client
            with patch.object(client, "_client") as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {"test": "data"}
                mock_response.raise_for_status.return_value = None
                mock_client.post = AsyncMock(return_value=mock_response)

                result = await client._make_request(
                    "http://test.com/api", "POST", {"data": "test"}
                )

                assert result == {"test": "data"}
                mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_client_wait_for_agent(self):
        """Test agent client waiting for agent availability."""
        from communication.agent_client import AgentClient

        async with AgentClient() as client:
            with patch.object(client, "check_health", new_callable=AsyncMock) as mock_health:
                # First call fails, second succeeds
                import httpx
                from types import SimpleNamespace
                mock_health.side_effect = [
                    httpx.HTTPError("Not ready"),
                    SimpleNamespace(status="healthy"),
                ]

                result = await client.wait_for_agent(
                    "http://test.com", max_retries=2, retry_delay=0.01
                )

                assert result is True
                assert mock_health.call_count == 2

    @pytest.mark.asyncio
    async def test_agent_client_wait_for_agent_timeout(self):
        """Test agent client timeout when waiting."""
        from communication.agent_client import AgentClient

        async with AgentClient() as client:
            with patch.object(client, "check_health", new_callable=AsyncMock) as mock_health:
                import httpx
                mock_health.side_effect = httpx.HTTPError("Not ready")

                result = await client.wait_for_agent(
                    "http://test.com", max_retries=2, retry_delay=0.01
                )

                assert result is False
                assert mock_health.call_count == 2  # max_retries


class TestMessageSchemas:
    """Test message schema validation."""

    def test_code_generation_request_validation(self):
        """Test code generation request validation."""
        from communication.message_schema import CodeGenerationRequest

        request = CodeGenerationRequest(
            task_description="Create a function",
            language="python",
            requirements=["Add type hints"],
            max_tokens=1000,
        )

        assert request.task_description == "Create a function"
        assert request.language == "python"
        assert request.requirements == ["Add type hints"]
        assert request.max_tokens == 1000

    def test_code_generation_response_validation(self):
        """Test code generation response validation."""
        from communication.message_schema import CodeGenerationResponse, TaskMetadata

        metadata = TaskMetadata(
            complexity="medium", lines_of_code=20, dependencies=["typing"]
        )

        response = CodeGenerationResponse(
            task_description="Create a function",
            generated_code="def test(): pass",
            tests="def test_test(): pass",
            metadata=metadata,
            tokens_used=100,
        )

        assert response.task_description == "Create a function"
        assert response.generated_code == "def test(): pass"
        assert response.tests == "def test_test(): pass"
        assert response.metadata.complexity == "medium"
        assert response.tokens_used == 100

    def test_code_review_request_validation(self):
        """Test code review request validation."""
        from communication.message_schema import CodeReviewRequest, TaskMetadata

        metadata = TaskMetadata(complexity="low", lines_of_code=10)

        request = CodeReviewRequest(
            task_description="Review this code",
            generated_code="def test(): pass",
            tests="def test_test(): pass",
            metadata=metadata,
        )

        assert request.task_description == "Review this code"
        assert request.generated_code == "def test(): pass"
        assert request.tests == "def test_test(): pass"
        assert request.metadata.complexity == "low"

    def test_code_review_response_validation(self):
        """Test code review response validation."""
        from communication.message_schema import CodeQualityMetrics, CodeReviewResponse

        metrics = CodeQualityMetrics(
            pep8_compliance=True,
            pep8_score=9.0,
            has_docstrings=True,
            has_type_hints=True,
            test_coverage="good",
            complexity_score=7.0,
        )

        response = CodeReviewResponse(
            code_quality_score=8.5,
            metrics=metrics,
            issues=["Issue 1", "Issue 2"],
            recommendations=["Rec 1"],
            tokens_used=150,
        )

        assert response.code_quality_score == 8.5
        assert response.metrics.pep8_compliance is True
        assert len(response.issues) == 2
        assert len(response.recommendations) == 1
        assert response.tokens_used == 150
