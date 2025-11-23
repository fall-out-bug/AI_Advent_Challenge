"""Unit tests for ResearchSkillAdapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResultStatus
from src.domain.god_agent.value_objects.skill import SkillType
from src.domain.rag import Answer, ComparisonResult, Query, RetrievedChunk
from src.infrastructure.god_agent.adapters.research_skill_adapter import (
    ResearchSkillAdapter,
)


@pytest.fixture
def mock_compare_rag_use_case():
    """Mock CompareRagAnswersUseCase."""
    use_case = AsyncMock()
    return use_case


@pytest.fixture
def research_adapter(mock_compare_rag_use_case):
    """Create ResearchSkillAdapter instance."""
    return ResearchSkillAdapter(compare_rag_answers_use_case=mock_compare_rag_use_case)


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
def sample_comparison_result():
    """Create sample ComparisonResult."""
    query = Query(id="q1", question="What is MapReduce?")
    answer = Answer(
        text="MapReduce is a programming model...",
        model="qwen",
        latency_ms=1500,
        tokens_generated=120,
    )
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        text="MapReduce — это модель программирования...",
        similarity_score=0.85,
        source_path="/docs/architecture.md",
        metadata={"ordinal": "0"},
    )
    return ComparisonResult(
        query=query,
        without_rag=answer,
        with_rag=answer,
        chunks_used=[chunk],
        timestamp="2024-01-01T00:00:00Z",
    )


@pytest.mark.asyncio
async def test_execute_calls_compare_rag_use_case(
    research_adapter,
    mock_compare_rag_use_case,
    sample_memory_snapshot,
    sample_comparison_result,
):
    """Test execute calls CompareRagAnswersUseCase."""
    # Setup mock
    mock_compare_rag_use_case.execute.return_value = sample_comparison_result

    # Execute
    input_data = {"query": "What is MapReduce?", "user_id": "user_123"}
    result = await research_adapter.execute(input_data, sample_memory_snapshot)

    # Verify
    assert result.status == SkillResultStatus.SUCCESS
    assert result.output is not None
    assert "answer" in result.output
    assert "citations" in result.output
    mock_compare_rag_use_case.execute.assert_called_once()


@pytest.mark.asyncio
async def test_execute_handles_use_case_error(
    research_adapter, mock_compare_rag_use_case, sample_memory_snapshot
):
    """Test execute handles CompareRagAnswersUseCase errors."""
    # Setup mock to raise error
    mock_compare_rag_use_case.execute.side_effect = Exception("Use case error")

    # Execute
    input_data = {"query": "What is MapReduce?", "user_id": "user_123"}
    result = await research_adapter.execute(input_data, sample_memory_snapshot)

    # Should return failure result
    assert result.status == SkillResultStatus.FAILURE
    assert result.error is not None
    assert "error" in result.error.lower()


@pytest.mark.asyncio
async def test_get_skill_id_returns_research(
    research_adapter,
):
    """Test get_skill_id returns research."""
    skill_id = research_adapter.get_skill_id()

    assert skill_id == SkillType.RESEARCH.value


@pytest.mark.asyncio
async def test_execute_creates_query_correctly(
    research_adapter,
    mock_compare_rag_use_case,
    sample_memory_snapshot,
    sample_comparison_result,
):
    """Test execute creates Query correctly."""
    mock_compare_rag_use_case.execute.return_value = sample_comparison_result

    input_data = {"query": "What is MapReduce?", "user_id": "user_123"}
    await research_adapter.execute(input_data, sample_memory_snapshot)

    # Verify Query was created correctly
    call_args = mock_compare_rag_use_case.execute.call_args
    assert call_args is not None
    query = call_args[0][0]
    assert isinstance(query, Query)
    assert query.question == "What is MapReduce?"


@pytest.mark.asyncio
async def test_execute_includes_citations_in_output(
    research_adapter,
    mock_compare_rag_use_case,
    sample_memory_snapshot,
    sample_comparison_result,
):
    """Test execute includes citations in output."""
    mock_compare_rag_use_case.execute.return_value = sample_comparison_result

    input_data = {"query": "What is MapReduce?", "user_id": "user_123"}
    result = await research_adapter.execute(input_data, sample_memory_snapshot)

    assert result.status == SkillResultStatus.SUCCESS
    assert result.output is not None
    assert "citations" in result.output
    assert len(result.output["citations"]) == 1
    assert result.output["citations"][0]["source_path"] == "/docs/architecture.md"
