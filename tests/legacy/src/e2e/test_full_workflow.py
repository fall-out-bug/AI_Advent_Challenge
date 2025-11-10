"""End-to-end tests for complete workflows.

Following TDD principles and the Zen of Python:
- Simple is better than complex
- Readability counts
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.application.orchestrators.multi_agent_orchestrator import (
    MultiAgentOrchestrator,
)
from src.application.use_cases.generate_code import GenerateCodeUseCase
from src.application.use_cases.review_code import ReviewCodeUseCase
from src.domain.messaging.message_schema import (
    CodeGenerationResponse,
    CodeQualityMetrics,
    CodeReviewResponse,
    OrchestratorRequest,
    TaskMetadata,
)
from src.infrastructure.clients.simple_model_client import SimpleModelClient
from src.infrastructure.repositories.json_agent_repository import JsonAgentRepository
from src.infrastructure.repositories.model_repository import InMemoryModelRepository


@pytest.fixture
def temp_storage_path() -> Path:
    """Create temporary storage path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        return Path(f.name)


@pytest.fixture
def services(temp_storage_path: Path):
    """Create all services for E2E testing."""
    agent_repo = JsonAgentRepository(temp_storage_path)
    model_repo = InMemoryModelRepository()
    model_client = SimpleModelClient()

    return {
        "agent_repo": agent_repo,
        "model_repo": model_repo,
        "model_client": model_client,
    }


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_full_code_generation_workflow(services: dict) -> None:
    """Test complete code generation workflow."""
    generate_use_case = GenerateCodeUseCase(
        agent_repository=services["agent_repo"],
        model_repository=services["model_repo"],
        model_client=services["model_client"],
    )

    task = await generate_use_case.execute(
        prompt="Create a function to add two numbers",
        agent_name="test_agent",
    )

    assert task is not None
    assert task.status.value == "completed"
    assert task.response is not None


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_full_code_review_workflow(services: dict) -> None:
    """Test complete code review workflow."""
    review_use_case = ReviewCodeUseCase(
        agent_repository=services["agent_repo"],
        model_repository=services["model_repo"],
        model_client=services["model_client"],
    )

    task = await review_use_case.execute(
        code="def add(a, b): return a + b",
        agent_name="test_agent",
    )

    assert task is not None
    assert task.task_type.value == "code_review"
    assert task.quality_metrics is not None


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_generate_and_review_workflow(services: dict) -> None:
    """Test generate then review workflow."""
    # Step 1: Generate code
    generate_use_case = GenerateCodeUseCase(
        agent_repository=services["agent_repo"],
        model_repository=services["model_repo"],
        model_client=services["model_client"],
    )

    generate_task = await generate_use_case.execute(
        prompt="Create a fibonacci function",
        agent_name="test_agent",
    )

    assert generate_task.is_completed()
    generated_code = generate_task.response or ""

    # Step 2: Review generated code
    review_use_case = ReviewCodeUseCase(
        agent_repository=services["agent_repo"],
        model_repository=services["model_repo"],
        model_client=services["model_client"],
    )

    review_task = await review_use_case.execute(
        code=generated_code,
        agent_name="test_agent",
    )

    assert review_task is not None
    assert review_task.task_type.value == "code_review"
    assert review_task.quality_metrics is not None


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_task_persistence(services: dict) -> None:
    """Test that tasks are persisted correctly."""
    generate_use_case = GenerateCodeUseCase(
        agent_repository=services["agent_repo"],
        model_repository=services["model_repo"],
        model_client=services["model_client"],
    )

    task = await generate_use_case.execute(
        prompt="Create a hello function",
        agent_name="test_agent",
    )

    task_id = task.task_id

    # Retrieve task from repository
    retrieved_task = await services["agent_repo"].get_by_id(task_id)

    assert retrieved_task is not None
    assert retrieved_task.task_id == task_id
    assert retrieved_task.prompt == "Create a hello function"


class TestFullPipelineScenarios:
    """Test full pipeline scenarios for E2E."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_multi_agent_collaboration_scenario(self):
        """Test multi-agent collaboration in complete pipeline."""
        # Setup mock orchestrator
        mock_generator = AsyncMock()
        mock_reviewer = AsyncMock()

        mock_generator.process.return_value = CodeGenerationResponse(
            task_description="Create REST API",
            generated_code="from fastapi import FastAPI\napp = FastAPI()",
            tests="def test_api(): pass",
            metadata=TaskMetadata(),
            generation_time=datetime.now(),
            tokens_used=100,
        )

        review_metrics = CodeQualityMetrics(
            pep8_compliance=True,
            pep8_score=9.0,
            has_docstrings=True,
            has_type_hints=True,
            test_coverage="excellent",
            complexity_score=2.0,
        )

        mock_reviewer.process.return_value = CodeReviewResponse(
            code_quality_score=9.0,
            metrics=review_metrics,
            issues=[],
            recommendations=[],
            review_time=datetime.now(),
            tokens_used=150,
        )

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        request = OrchestratorRequest(
            task_description="Create REST API",
            language="python",
            model_name="starcoder",
        )

        # Execute full pipeline
        response = await orchestrator.process_task(request)

        # Verify complete pipeline
        assert response.success is True
        assert response.generation_result is not None
        assert response.review_result is not None
        assert response.workflow_time > 0

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_token_limit_handling_with_auto_compression(self):
        """Test handling token limits with auto-compression."""
        from src.domain.services.token_analyzer import TokenAnalyzer

        # Create text that exceeds limits
        long_text = " ".join(["word"] * 10000)

        # Apply auto-compression
        compressed_text, metadata = TokenAnalyzer.analyze_and_compress(
            long_text, model_name="starcoder"
        )

        # Verify compression was applied
        assert metadata["compression_applied"] is True
        assert len(compressed_text) < len(long_text)
        assert "original_tokens" in metadata
        assert "compressed_tokens" in metadata

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_model_switching_during_workflow(self):
        """Test switching models during workflow execution."""
        from src.application.orchestrators.parallel_orchestrator import (
            ParallelOrchestrator,
        )

        orchestrator = ParallelOrchestrator()

        # Create tasks with different models
        tasks = []
        for model_name in ["starcoder", "mistral"]:
            agent = AsyncMock()
            agent.process.return_value = f"Result from {model_name}"
            tasks.append((agent, None))

        # Execute parallel
        results = await orchestrator.execute_parallel(tasks, fail_fast=False)

        assert len(results) == 2
        assert any("starcoder" in str(r) for r in results if isinstance(r, str))
        assert any("mistral" in str(r) for r in results if isinstance(r, str))

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_end_to_end_error_recovery(self):
        """Test end-to-end error recovery in workflow."""
        # Setup orchestrator with failing generator
        mock_generator = AsyncMock()
        mock_generator.process.side_effect = Exception("Model unavailable")

        orchestrator = MultiAgentOrchestrator(generator_agent=mock_generator)

        request = OrchestratorRequest(
            task_description="Test error recovery",
            model_name="starcoder",
        )

        # Execute - should handle error gracefully
        response = await orchestrator.process_task(request)

        # Verify error handling
        assert response.success is False
        assert response.error_message is not None
        # Error message contains relevant information
        error_lower = response.error_message.lower()
        assert "model" in error_lower or "error" in error_lower or "fail" in error_lower

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_code_generation_pipeline(self):
        """Test complete pipeline from request to response."""
        mock_generator = AsyncMock()
        mock_reviewer = AsyncMock()

        mock_generator.process.return_value = CodeGenerationResponse(
            task_description="Create calculator",
            generated_code="def calc(): return 42",
            tests="def test_calc(): assert calc() == 42",
            metadata=TaskMetadata(),
            generation_time=datetime.now(),
            tokens_used=100,
        )

        mock_reviewer.process.return_value = CodeReviewResponse(
            code_quality_score=8.5,
            metrics=CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=8.5,
                has_docstrings=True,
                has_type_hints=False,
                test_coverage="good",
                complexity_score=2.0,
            ),
            issues=[],
            recommendations=[],
            review_time=datetime.now(),
            tokens_used=150,
        )

        orchestrator = MultiAgentOrchestrator(
            generator_agent=mock_generator,
            reviewer_agent=mock_reviewer,
        )

        # Request -> Pipeline -> Response
        request = OrchestratorRequest(
            task_description="Create calculator",
            language="python",
            model_name="starcoder",
        )

        response = await orchestrator.process_task(request)

        # Verify complete pipeline
        assert response.success is True
        assert response.task_description == "Create calculator"
        assert response.generation_result.generated_code == "def calc(): return 42"
        assert response.review_result.code_quality_score == 8.5
