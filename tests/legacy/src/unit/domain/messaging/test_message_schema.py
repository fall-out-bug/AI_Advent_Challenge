"""Unit tests for message schemas.

Following TDD principles and the Zen of Python:
- Tests should be simple and readable
- One test per behavior
- Clear assertions
"""

from datetime import datetime

import pytest

from src.domain.messaging.message_schema import (
    AgentHealthResponse,
    AgentStatsResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
    CodeQualityMetrics,
    CodeReviewRequest,
    CodeReviewResponse,
    OrchestratorRequest,
    OrchestratorResponse,
    TaskMetadata,
)


def test_task_metadata_creation():
    """Test task metadata creation."""
    metadata = TaskMetadata(
        complexity="high",
        lines_of_code=50,
        estimated_time="10 minutes",
        dependencies=["requests", "pydantic"],
    )

    assert metadata.complexity == "high"
    assert metadata.lines_of_code == 50
    assert metadata.estimated_time == "10 minutes"
    assert metadata.dependencies == ["requests", "pydantic"]


def test_task_metadata_defaults():
    """Test task metadata with default values."""
    metadata = TaskMetadata()

    assert metadata.complexity == "medium"
    assert metadata.lines_of_code == 0
    assert metadata.estimated_time is None
    assert metadata.dependencies == []


def test_task_metadata_to_dict():
    """Test converting metadata to dictionary."""
    metadata = TaskMetadata(
        complexity="low",
        lines_of_code=10,
        dependencies=["test"],
    )

    data = metadata.to_dict()

    assert data["complexity"] == "low"
    assert data["lines_of_code"] == 10
    assert data["dependencies"] == ["test"]


def test_code_generation_request_creation():
    """Test code generation request creation."""
    request = CodeGenerationRequest(
        task_description="Create a function",
        language="python",
        requirements=["type hints", "docstrings"],
        max_tokens=1500,
        model_name="starcoder",
    )

    assert request.task_description == "Create a function"
    assert request.language == "python"
    assert request.requirements == ["type hints", "docstrings"]
    assert request.max_tokens == 1500
    assert request.model_name == "starcoder"


def test_code_generation_request_defaults():
    """Test code generation request with defaults."""
    request = CodeGenerationRequest(task_description="Create a function")

    assert request.language == "python"
    assert request.requirements == []
    assert request.max_tokens == 1000
    assert request.model_name == "starcoder"


def test_code_generation_response_creation():
    """Test code generation response creation."""
    metadata = TaskMetadata(complexity="medium", lines_of_code=20)
    response = CodeGenerationResponse(
        task_description="Create a function",
        generated_code="def hello(): pass",
        tests="def test_hello(): assert hello() is None",
        metadata=metadata,
        tokens_used=150,
    )

    assert response.task_description == "Create a function"
    assert "def hello()" in response.generated_code
    assert "def test_hello()" in response.tests
    assert isinstance(response.generation_time, datetime)
    assert response.tokens_used == 150


def test_code_quality_metrics_creation():
    """Test code quality metrics creation."""
    metrics = CodeQualityMetrics(
        pep8_compliance=True,
        pep8_score=8.5,
        has_docstrings=True,
        has_type_hints=True,
        test_coverage="good",
        complexity_score=3.0,
    )

    assert metrics.pep8_compliance is True
    assert metrics.pep8_score == 8.5
    assert metrics.has_docstrings is True
    assert metrics.has_type_hints is True
    assert metrics.test_coverage == "good"
    assert metrics.complexity_score == 3.0


def test_code_review_request_creation():
    """Test code review request creation."""
    metadata = TaskMetadata(complexity="medium")
    request = CodeReviewRequest(
        task_description="Review function",
        generated_code="def test(): pass",
        tests="def test_test(): pass",
        metadata=metadata,
    )

    assert request.task_description == "Review function"
    assert request.generated_code == "def test(): pass"
    assert request.tests == "def test_test(): pass"


def test_code_review_response_creation():
    """Test code review response creation."""
    metrics = CodeQualityMetrics(
        pep8_compliance=True,
        pep8_score=8.0,
        has_docstrings=True,
        has_type_hints=True,
        test_coverage="excellent",
        complexity_score=2.0,
    )

    response = CodeReviewResponse(
        code_quality_score=8.5,
        metrics=metrics,
        issues=["Minor formatting issue"],
        recommendations=["Add more tests"],
        tokens_used=200,
    )

    assert response.code_quality_score == 8.5
    assert response.issues == ["Minor formatting issue"]
    assert response.recommendations == ["Add more tests"]
    assert isinstance(response.review_time, datetime)
    assert response.tokens_used == 200


def test_orchestrator_request_creation():
    """Test orchestrator request creation."""
    request = OrchestratorRequest(
        task_description="Create and review function",
        language="python",
        requirements=["type hints"],
        model_name="starcoder",
        reviewer_model_name="mistral",
    )

    assert request.task_description == "Create and review function"
    assert request.language == "python"
    assert request.requirements == ["type hints"]
    assert request.model_name == "starcoder"
    assert request.reviewer_model_name == "mistral"


def test_orchestrator_request_default_reviewer():
    """Test orchestrator request with default reviewer model."""
    request = OrchestratorRequest(
        task_description="Create and review",
        model_name="starcoder",
    )

    assert request.reviewer_model_name is None


def test_orchestrator_response_success():
    """Test orchestrator response for successful workflow."""
    gen_response = CodeGenerationResponse(
        task_description="Test",
        generated_code="def test(): pass",
        tests="def test_test(): pass",
        metadata=TaskMetadata(),
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
        tokens_used=150,
    )

    orchestrator_response = OrchestratorResponse(
        task_description="Test",
        success=True,
        generation_result=gen_response,
        review_result=review_response,
        workflow_time=5.5,
    )

    assert orchestrator_response.success is True
    assert orchestrator_response.generation_result is not None
    assert orchestrator_response.review_result is not None
    assert orchestrator_response.workflow_time == 5.5


def test_orchestrator_response_failure():
    """Test orchestrator response for failed workflow."""
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


def test_agent_health_response():
    """Test agent health response."""
    response = AgentHealthResponse(
        status="healthy",
        agent_type="generator",
        uptime=3600.0,
        last_request=datetime.now(),
    )

    assert response.status == "healthy"
    assert response.agent_type == "generator"
    assert response.uptime == 3600.0
    assert isinstance(response.last_request, datetime)


def test_agent_stats_response():
    """Test agent stats response."""
    response = AgentStatsResponse(
        total_requests=100,
        successful_requests=95,
        failed_requests=5,
        average_response_time=1.5,
        total_tokens_used=5000,
    )

    assert response.total_requests == 100
    assert response.successful_requests == 95
    assert response.failed_requests == 5
    assert response.average_response_time == 1.5
    assert response.total_tokens_used == 5000


def test_validation_errors():
    """Test that validation errors are raised for invalid data."""
    # Invalid PEP8 score (out of range)
    with pytest.raises(Exception):
        CodeQualityMetrics(
            pep8_compliance=True,
            pep8_score=15.0,  # Invalid: should be 0-10
            has_docstrings=True,
            has_type_hints=True,
            test_coverage="good",
            complexity_score=2.0,
        )

    # Invalid code quality score
    with pytest.raises(Exception):
        CodeReviewResponse(
            code_quality_score=15.0,  # Invalid: should be 0-10
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
            tokens_used=100,
        )
