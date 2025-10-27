"""Unit tests for multi-agent orchestrator.

Following TDD principles and the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.application.orchestrators.multi_agent_orchestrator import (
    MultiAgentOrchestrator,
)
from src.domain.agents.code_generator import CodeGeneratorAgent
from src.domain.agents.code_reviewer import CodeReviewerAgent
from src.domain.messaging.message_schema import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    CodeQualityMetrics,
    CodeReviewRequest,
    CodeReviewResponse,
    OrchestratorRequest,
    OrchestratorResponse,
    TaskMetadata,
)


class TestMultiAgentOrchestratorInitialization:
    """Test orchestrator initialization."""

    def test_init_with_default_agents(self):
        """Test initialization with default agents."""
        orchestrator = MultiAgentOrchestrator()

        assert orchestrator.generator is not None
        assert orchestrator.reviewer is not None
        assert isinstance(orchestrator.generator, CodeGeneratorAgent)
        assert isinstance(orchestrator.reviewer, CodeReviewerAgent)

    def test_init_with_custom_agents(self):
        """Test initialization with custom agents."""
        custom_generator = CodeGeneratorAgent()
        custom_reviewer = CodeReviewerAgent()

        orchestrator = MultiAgentOrchestrator(
            generator_agent=custom_generator,
            reviewer_agent=custom_reviewer,
        )

        assert orchestrator.generator is custom_generator
        assert orchestrator.reviewer is custom_reviewer

    def test_initial_stats(self):
        """Test initial statistics are set correctly."""
        orchestrator = MultiAgentOrchestrator()

        stats = orchestrator.get_stats()
        assert stats["total_workflows"] == 0
        assert stats["successful_workflows"] == 0
        assert stats["failed_workflows"] == 0
        assert stats["average_workflow_time"] == 0.0


class TestMultiAgentOrchestratorProcessTask:
    """Test orchestrator task processing."""

    @pytest.mark.asyncio
    async def test_process_task_successful_workflow(self):
        """Test successful workflow processing."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_reviewer = AsyncMock(spec=CodeReviewerAgent)

        # Setup mock responses
        gen_response = CodeGenerationResponse(
            task_description="Create hello function",
            generated_code="def hello(): print('Hello')",
            tests="def test_hello(): pass",
            metadata=TaskMetadata(),
            generation_time=datetime.now(),
            tokens_used=100,
        )

        review_metrics = CodeQualityMetrics(
            pep8_compliance=True,
            pep8_score=8.0,
            has_docstrings=True,
            has_type_hints=True,
            test_coverage="good",
            complexity_score=2.0,
        )

        review_response = CodeReviewResponse(
            code_quality_score=8.5,
            metrics=review_metrics,
            issues=[],
            recommendations=[],
            review_time=datetime.now(),
            tokens_used=150,
        )

        mock_generator.process.return_value = gen_response
        mock_reviewer.process.return_value = review_response

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        request = OrchestratorRequest(
            task_description="Create hello function",
            language="python",
            model_name="starcoder",
        )

        # Act
        response = await orchestrator.process_task(request)

        # Assert
        assert response.success is True
        assert response.generation_result is not None
        assert response.review_result is not None
        assert response.workflow_time > 0
        assert mock_generator.process.called
        assert mock_reviewer.process.called

    @pytest.mark.asyncio
    async def test_process_task_failed_workflow(self):
        """Test failed workflow processing."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_generator.process.side_effect = Exception("Generation failed")

        orchestrator = MultiAgentOrchestrator(generator_agent=mock_generator)

        request = OrchestratorRequest(
            task_description="Test task",
            model_name="starcoder",
        )

        # Act
        response = await orchestrator.process_task(request)

        # Assert
        assert response.success is False
        assert response.error_message is not None
        assert "Generation failed" in response.error_message

    @pytest.mark.asyncio
    async def test_process_task_with_reviewer_model_name(self):
        """Test processing with separate reviewer model."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_reviewer = AsyncMock(spec=CodeReviewerAgent)

        gen_response = CodeGenerationResponse(
            task_description="Test",
            generated_code="code",
            tests="tests",
            metadata=TaskMetadata(),
            tokens_used=100,
        )

        review_response = CodeReviewResponse(
            code_quality_score=7.0,
            metrics=CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=7.0,
                has_docstrings=False,
                has_type_hints=False,
                test_coverage="basic",
                complexity_score=3.0,
            ),
            issues=[],
            recommendations=[],
            tokens_used=150,
        )

        mock_generator.process.return_value = gen_response
        mock_reviewer.process.return_value = review_response

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        request = OrchestratorRequest(
            task_description="Test task",
            model_name="starcoder",
            reviewer_model_name="mistral",
        )

        # Act
        await orchestrator.process_task(request)

        # Assert
        assert mock_reviewer.process.called

    @pytest.mark.asyncio
    async def test_process_task_workflow_time_tracking(self):
        """Test workflow time is tracked correctly."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_reviewer = AsyncMock(spec=CodeReviewerAgent)

        mock_generator.process.return_value = CodeGenerationResponse(
            task_description="Test",
            generated_code="code",
            tests="tests",
            metadata=TaskMetadata(),
            tokens_used=100,
        )

        mock_reviewer.process.return_value = CodeReviewResponse(
            code_quality_score=7.0,
            metrics=CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=7.0,
                has_docstrings=False,
                has_type_hints=False,
                test_coverage="basic",
                complexity_score=3.0,
            ),
            issues=[],
            recommendations=[],
            tokens_used=150,
        )

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        request = OrchestratorRequest(
            task_description="Test task",
            model_name="starcoder",
        )

        # Act
        response = await orchestrator.process_task(request)

        # Assert
        assert response.workflow_time >= 0
        assert isinstance(response.workflow_time, float)


class TestMultiAgentOrchestratorStatistics:
    """Test orchestrator statistics tracking."""

    @pytest.mark.asyncio
    async def test_stats_track_successful_workflows(self):
        """Test statistics track successful workflows."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_reviewer = AsyncMock(spec=CodeReviewerAgent)

        mock_generator.process.return_value = CodeGenerationResponse(
            task_description="Test",
            generated_code="code",
            tests="tests",
            metadata=TaskMetadata(),
            tokens_used=100,
        )

        mock_reviewer.process.return_value = CodeReviewResponse(
            code_quality_score=8.0,
            metrics=CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=8.0,
                has_docstrings=True,
                has_type_hints=True,
                test_coverage="good",
                complexity_score=2.0,
            ),
            issues=[],
            recommendations=[],
            tokens_used=150,
        )

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        request = OrchestratorRequest(
            task_description="Test task",
            model_name="starcoder",
        )

        # Act
        await orchestrator.process_task(request)

        # Assert
        stats = orchestrator.get_stats()
        assert stats["total_workflows"] == 1
        assert stats["successful_workflows"] == 1
        assert stats["failed_workflows"] == 0

    @pytest.mark.asyncio
    async def test_stats_track_failed_workflows(self):
        """Test statistics track failed workflows."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_generator.process.side_effect = Exception("Test error")

        orchestrator = MultiAgentOrchestrator(generator_agent=mock_generator)

        request = OrchestratorRequest(
            task_description="Test task",
            model_name="starcoder",
        )

        # Act
        await orchestrator.process_task(request)

        # Assert
        stats = orchestrator.get_stats()
        assert stats["total_workflows"] == 1
        assert stats["successful_workflows"] == 0
        assert stats["failed_workflows"] == 1

    @pytest.mark.asyncio
    async def test_average_workflow_time_calculation(self):
        """Test average workflow time calculation."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_reviewer = AsyncMock(spec=CodeReviewerAgent)

        mock_generator.process.return_value = CodeGenerationResponse(
            task_description="Test",
            generated_code="code",
            tests="tests",
            metadata=TaskMetadata(),
            tokens_used=100,
        )

        mock_reviewer.process.return_value = CodeReviewResponse(
            code_quality_score=8.0,
            metrics=CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=8.0,
                has_docstrings=True,
                has_type_hints=True,
                test_coverage="good",
                complexity_score=2.0,
            ),
            issues=[],
            recommendations=[],
            tokens_used=150,
        )

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        request = OrchestratorRequest(
            task_description="Test task",
            model_name="starcoder",
        )

        # Act - run multiple workflows
        await orchestrator.process_task(request)
        await orchestrator.process_task(request)

        # Assert
        stats = orchestrator.get_stats()
        assert stats["average_workflow_time"] >= 0

    def test_get_stats_returns_copy(self):
        """Test get_stats returns a copy of statistics."""
        orchestrator = MultiAgentOrchestrator()

        stats1 = orchestrator.get_stats()
        stats1["total_workflows"] = 999

        stats2 = orchestrator.get_stats()
        assert stats2["total_workflows"] == 0

    def test_reset_stats(self):
        """Test resetting statistics."""
        orchestrator = MultiAgentOrchestrator()

        # Modify stats directly
        orchestrator.stats["total_workflows"] = 5
        orchestrator.stats["successful_workflows"] = 3

        # Reset
        orchestrator.reset_stats()

        # Verify
        stats = orchestrator.get_stats()
        assert stats["total_workflows"] == 0
        assert stats["successful_workflows"] == 0
        assert stats["failed_workflows"] == 0
        assert stats["average_workflow_time"] == 0.0


class TestMultiAgentOrchestratorErrorHandling:
    """Test orchestrator error handling."""

    @pytest.mark.asyncio
    async def test_handles_generation_error(self):
        """Test handling of generation errors."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_generator.process.side_effect = Exception("Generation error")

        orchestrator = MultiAgentOrchestrator(generator_agent=mock_generator)

        request = OrchestratorRequest(
            task_description="Test task",
            model_name="starcoder",
        )

        # Act
        response = await orchestrator.process_task(request)

        # Assert
        assert response.success is False
        assert response.error_message is not None
        assert response.generation_result is None
        assert response.review_result is None

    @pytest.mark.asyncio
    async def test_handles_review_error(self):
        """Test handling of review errors."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_reviewer = AsyncMock(spec=CodeReviewerAgent)

        mock_generator.process.return_value = CodeGenerationResponse(
            task_description="Test",
            generated_code="code",
            tests="tests",
            metadata=TaskMetadata(),
            tokens_used=100,
        )

        mock_reviewer.process.side_effect = Exception("Review error")

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        request = OrchestratorRequest(
            task_description="Test task",
            model_name="starcoder",
        )

        # Act
        response = await orchestrator.process_task(request)

        # Assert
        assert response.success is False
        assert response.error_message is not None


class TestMultiAgentOrchestratorWorkflowSteps:
    """Test individual workflow steps."""

    @pytest.mark.asyncio
    async def test_generate_code_step(self):
        """Test code generation step."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)

        expected_response = CodeGenerationResponse(
            task_description="Create hello",
            generated_code="def hello(): pass",
            tests="def test_hello(): pass",
            metadata=TaskMetadata(),
            tokens_used=100,
        )

        mock_generator.process.return_value = expected_response

        orchestrator = MultiAgentOrchestrator(generator_agent=mock_generator)

        request = OrchestratorRequest(
            task_description="Create hello",
            language="python",
            model_name="starcoder",
        )

        # Act
        result = await orchestrator._generate_code_step(request)

        # Assert
        assert result is expected_response
        mock_generator.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_code_step(self):
        """Test code review step."""
        # Arrange
        mock_reviewer = AsyncMock(spec=CodeReviewerAgent)

        generation_result = CodeGenerationResponse(
            task_description="Create hello",
            generated_code="def hello(): pass",
            tests="def test_hello(): pass",
            metadata=TaskMetadata(),
            tokens_used=100,
        )

        expected_review = CodeReviewResponse(
            code_quality_score=8.0,
            metrics=CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=8.0,
                has_docstrings=True,
                has_type_hints=True,
                test_coverage="good",
                complexity_score=2.0,
            ),
            issues=[],
            recommendations=[],
            tokens_used=150,
        )

        mock_reviewer.process.return_value = expected_review

        orchestrator = MultiAgentOrchestrator(reviewer_agent=mock_reviewer)

        request = OrchestratorRequest(
            task_description="Create hello",
            model_name="starcoder",
        )

        # Act
        result = await orchestrator._review_code_step(request, generation_result)

        # Assert
        assert result is expected_review
        mock_reviewer.process.assert_called_once()


class TestMultiAgentOrchestratorMultipleWorkflows:
    """Test orchestrator with multiple workflows."""

    @pytest.mark.asyncio
    async def test_multiple_sequential_workflows(self):
        """Test multiple sequential workflows."""
        # Arrange
        mock_generator = AsyncMock(spec=CodeGeneratorAgent)
        mock_reviewer = AsyncMock(spec=CodeReviewerAgent)

        mock_generator.process.return_value = CodeGenerationResponse(
            task_description="Test",
            generated_code="code",
            tests="tests",
            metadata=TaskMetadata(),
            tokens_used=100,
        )

        mock_reviewer.process.return_value = CodeReviewResponse(
            code_quality_score=8.0,
            metrics=CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=8.0,
                has_docstrings=True,
                has_type_hints=True,
                test_coverage="good",
                complexity_score=2.0,
            ),
            issues=[],
            recommendations=[],
            tokens_used=150,
        )

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        request1 = OrchestratorRequest(
            task_description="Task 1",
            model_name="starcoder",
        )

        request2 = OrchestratorRequest(
            task_description="Task 2",
            model_name="mistral",
        )

        # Act
        response1 = await orchestrator.process_task(request1)
        response2 = await orchestrator.process_task(request2)

        # Assert
        assert response1.success is True
        assert response2.success is True

        stats = orchestrator.get_stats()
        assert stats["total_workflows"] == 2
        assert stats["successful_workflows"] == 2
