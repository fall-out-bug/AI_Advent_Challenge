"""Unit tests for ReviewerSkillAdapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dtos.homework_dtos import HomeworkReviewResult
from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResultStatus
from src.domain.god_agent.value_objects.skill import SkillType
from src.infrastructure.god_agent.adapters.reviewer_skill_adapter import (
    ReviewerSkillAdapter,
)


@pytest.fixture
def mock_review_homework_use_case():
    """Mock ReviewHomeworkUseCase."""
    use_case = AsyncMock()
    return use_case


@pytest.fixture
def reviewer_adapter(mock_review_homework_use_case):
    """Create ReviewerSkillAdapter instance."""
    return ReviewerSkillAdapter(review_homework_use_case=mock_review_homework_use_case)


@pytest.fixture
def sample_memory_snapshot():
    """Create sample MemorySnapshot."""
    return MemorySnapshot(
        user_id="user_123",
        profile_summary="Persona: Alfred | Language: en",
        conversation_summary="Recent chat",
        rag_hits=[],
        artifact_refs=[],
    )


@pytest.fixture
def sample_review_result():
    """Create sample HomeworkReviewResult."""
    return HomeworkReviewResult(
        success=True,
        markdown_report="# Review Report\n\nFound 5 issues.",
        total_findings=5,
        detected_components=["component1", "component2"],
        pass_2_components=["component1"],
        execution_time_seconds=10.5,
    )


@pytest.mark.asyncio
async def test_execute_calls_review_homework_use_case(
    reviewer_adapter,
    mock_review_homework_use_case,
    sample_memory_snapshot,
    sample_review_result,
):
    """Test execute calls ReviewHomeworkUseCase."""
    # Setup mock
    mock_review_homework_use_case.execute.return_value = sample_review_result

    # Execute
    input_data = {"commit_hash": "abc123", "user_id": "user_123"}
    result = await reviewer_adapter.execute(input_data, sample_memory_snapshot)

    # Verify
    assert result.status == SkillResultStatus.SUCCESS
    assert result.output is not None
    assert "report" in result.output
    assert "total_findings" in result.output
    mock_review_homework_use_case.execute.assert_called_once()


@pytest.mark.asyncio
async def test_execute_handles_use_case_error(
    reviewer_adapter, mock_review_homework_use_case, sample_memory_snapshot
):
    """Test execute handles ReviewHomeworkUseCase errors."""
    # Setup mock to raise error
    mock_review_homework_use_case.execute.side_effect = Exception("Review error")

    # Execute
    input_data = {"commit_hash": "abc123", "user_id": "user_123"}
    result = await reviewer_adapter.execute(input_data, sample_memory_snapshot)

    # Should return failure result
    assert result.status == SkillResultStatus.FAILURE
    assert result.error is not None
    assert "error" in result.error.lower()


@pytest.mark.asyncio
async def test_get_skill_id_returns_reviewer(
    reviewer_adapter,
):
    """Test get_skill_id returns reviewer."""
    skill_id = reviewer_adapter.get_skill_id()

    assert skill_id == SkillType.REVIEWER.value


@pytest.mark.asyncio
async def test_execute_uses_commit_hash_correctly(
    reviewer_adapter,
    mock_review_homework_use_case,
    sample_memory_snapshot,
    sample_review_result,
):
    """Test execute uses commit_hash correctly."""
    mock_review_homework_use_case.execute.return_value = sample_review_result

    input_data = {"commit_hash": "abc123", "user_id": "user_123"}
    await reviewer_adapter.execute(input_data, sample_memory_snapshot)

    # Verify commit_hash was used correctly
    call_args = mock_review_homework_use_case.execute.call_args
    assert call_args is not None
    commit_hash = call_args[0][0]
    assert commit_hash == "abc123"
