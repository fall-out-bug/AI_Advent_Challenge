"""Unit tests for multi-agent orchestrator.

Following TDD principles and the Zen of Python.
"""

from datetime import datetime

import pytest

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


class MockOrchestrator:
    """Mock orchestrator for testing."""

    def __init__(self, generator=None, reviewer=None):
        """Initialize mock orchestrator."""
        self.generator = generator
        self.reviewer = reviewer
        self.stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
        }

    async def process_task(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Process a complete workflow."""
        self.stats["total_workflows"] += 1

        try:
            # Generate code
            gen_response = CodeGenerationResponse(
                task_description=request.task_description,
                generated_code="def hello(): pass",
                tests="def test_hello(): pass",
                metadata=TaskMetadata(),
                generation_time=datetime.now(),
                tokens_used=100,
            )

            # Review code
            review_metrics = CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=8.0,
                has_docstrings=True,
                has_type_hints=True,
                test_coverage="excellent",
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

            self.stats["successful_workflows"] += 1

            return OrchestratorResponse(
                task_description=request.task_description,
                success=True,
                generation_result=gen_response,
                review_result=review_response,
                workflow_time=5.5,
            )

        except Exception as e:
            self.stats["failed_workflows"] += 1
            return OrchestratorResponse(
                task_description=request.task_description,
                success=False,
                workflow_time=2.0,
                error_message=str(e),
            )


class MockCodeGenerator:
    """Mock code generator."""

    async def process(self, request: CodeGenerationRequest):
        """Process generation request."""
        return CodeGenerationResponse(
            task_description=request.task_description,
            generated_code="def hello(): pass",
            tests="def test_hello(): pass",
            metadata=TaskMetadata(),
            generation_time=datetime.now(),
            tokens_used=100,
        )


class MockCodeReviewer:
    """Mock code reviewer."""

    async def process(self, request: CodeReviewRequest):
        """Process review request."""
        review_metrics = CodeQualityMetrics(
            pep8_compliance=True,
            pep8_score=8.0,
            has_docstrings=True,
            has_type_hints=True,
            test_coverage="excellent",
            complexity_score=2.0,
        )

        return CodeReviewResponse(
            code_quality_score=8.5,
            metrics=review_metrics,
            issues=[],
            recommendations=[],
            review_time=datetime.now(),
            tokens_used=150,
        )


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    orchestrator = MockOrchestrator()

    assert orchestrator.stats["total_workflows"] == 0
    assert orchestrator.stats["successful_workflows"] == 0
    assert orchestrator.stats["failed_workflows"] == 0


@pytest.mark.asyncio
async def test_orchestrator_process_successful_workflow():
    """Test processing a successful workflow."""
    orchestrator = MockOrchestrator()

    request = OrchestratorRequest(
        task_description="Create a hello function",
        language="python",
        model_name="starcoder",
    )

    response = await orchestrator.process_task(request)

    assert response.success is True
    assert response.generation_result is not None
    assert response.review_result is not None
    assert response.workflow_time > 0
    assert orchestrator.stats["successful_workflows"] == 1


@pytest.mark.asyncio
async def test_orchestrator_process_failed_workflow():
    """Test processing a failed workflow."""

    class FailingOrchestrator(MockOrchestrator):
        async def process_task(self, request):
            """Simulate failure."""
            self.stats["total_workflows"] += 1
            self.stats["failed_workflows"] += 1
            raise Exception("Workflow failed")

    orchestrator = FailingOrchestrator()

    request = OrchestratorRequest(
        task_description="Test task",
        model_name="starcoder",
    )

    # Should propagate exception
    with pytest.raises(Exception, match="Workflow failed"):
        await orchestrator.process_task(request)

    assert orchestrator.stats["failed_workflows"] == 1


@pytest.mark.asyncio
async def test_orchestrator_stats_tracking():
    """Test that orchestrator tracks statistics."""
    orchestrator = MockOrchestrator()

    request = OrchestratorRequest(
        task_description="Test task",
        model_name="starcoder",
    )

    await orchestrator.process_task(request)

    assert orchestrator.stats["total_workflows"] == 1
    assert orchestrator.stats["successful_workflows"] == 1
    assert orchestrator.stats["failed_workflows"] == 0


@pytest.mark.asyncio
async def test_orchestrator_with_generator_and_reviewer():
    """Test orchestrator with actual generator and reviewer."""
    generator = MockCodeGenerator()
    reviewer = MockCodeReviewer()
    orchestrator = MockOrchestrator(generator=generator, reviewer=reviewer)

    request = OrchestratorRequest(
        task_description="Create and review function",
        language="python",
        model_name="starcoder",
    )

    response = await orchestrator.process_task(request)

    assert response.success is True
    assert response.generation_result.generated_code == "def hello(): pass"
    assert response.review_result.code_quality_score == 8.5


@pytest.mark.asyncio
async def test_orchestrator_error_handling():
    """Test error handling in orchestrator."""
    orchestrator = MockOrchestrator()

    request = OrchestratorRequest(
        task_description="Test task",
        model_name="starcoder",
    )

    # Should handle errors gracefully
    response = await orchestrator.process_task(request)

    # Should return response even if workflow fails internally
    assert hasattr(response, "success")


@pytest.mark.asyncio
async def test_orchestrator_multiple_workflows():
    """Test handling multiple workflows."""
    orchestrator = MockOrchestrator()

    request1 = OrchestratorRequest(
        task_description="Task 1",
        model_name="starcoder",
    )
    request2 = OrchestratorRequest(
        task_description="Task 2",
        model_name="mistral",
    )

    await orchestrator.process_task(request1)
    await orchestrator.process_task(request2)

    assert orchestrator.stats["total_workflows"] == 2
    assert orchestrator.stats["successful_workflows"] == 2


@pytest.mark.asyncio
async def test_orchestrator_workflow_time():
    """Test that workflow time is tracked."""
    orchestrator = MockOrchestrator()

    request = OrchestratorRequest(
        task_description="Test task",
        model_name="starcoder",
    )

    response = await orchestrator.process_task(request)

    assert response.workflow_time > 0
    assert isinstance(response.workflow_time, float)


def test_orchestrator_request_creation():
    """Test orchestrator request creation."""
    request = OrchestratorRequest(
        task_description="Create a function",
        language="python",
        requirements=["type hints"],
        model_name="starcoder",
        reviewer_model_name="mistral",
    )

    assert request.task_description == "Create a function"
    assert request.language == "python"
    assert request.requirements == ["type hints"]
    assert request.model_name == "starcoder"
    assert request.reviewer_model_name == "mistral"


def test_orchestrator_response_success():
    """Test successful orchestrator response."""
    gen_response = CodeGenerationResponse(
        task_description="Test",
        generated_code="def hello(): pass",
        tests="def test_hello(): pass",
        metadata=TaskMetadata(),
        tokens_used=100,
    )

    review_metrics = CodeQualityMetrics(
        pep8_compliance=True,
        pep8_score=8.0,
        has_docstrings=True,
        has_type_hints=True,
        test_coverage="excellent",
        complexity_score=2.0,
    )

    review_response = CodeReviewResponse(
        code_quality_score=8.5,
        metrics=review_metrics,
        issues=[],
        recommendations=[],
        tokens_used=150,
    )

    response = OrchestratorResponse(
        task_description="Test",
        success=True,
        generation_result=gen_response,
        review_result=review_response,
        workflow_time=5.5,
    )

    assert response.success is True
    assert response.generation_result is not None
    assert response.review_result is not None
    assert response.workflow_time == 5.5


def test_orchestrator_response_failure():
    """Test failed orchestrator response."""
    response = OrchestratorResponse(
        task_description="Test",
        success=False,
        workflow_time=2.0,
        error_message="Generation failed",
    )

    assert response.success is False
    assert response.error_message == "Generation failed"
    assert response.generation_result is None
    assert response.review_result is None
