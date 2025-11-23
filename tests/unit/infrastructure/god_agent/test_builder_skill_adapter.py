"""Unit tests for BuilderSkillAdapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.god_agent.entities.memory_snapshot import MemorySnapshot
from src.domain.god_agent.entities.skill_result import SkillResultStatus
from src.domain.god_agent.value_objects.skill import SkillType
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.infrastructure.god_agent.adapters.builder_skill_adapter import (
    BuilderSkillAdapter,
)


@pytest.fixture
def mock_generate_code_use_case():
    """Mock GenerateCodeUseCase."""
    use_case = AsyncMock()
    return use_case


@pytest.fixture
def mock_generate_tests_use_case():
    """Mock GenerateTestsUseCase."""
    use_case = AsyncMock()
    return use_case


@pytest.fixture
def builder_adapter(mock_generate_code_use_case, mock_generate_tests_use_case):
    """Create BuilderSkillAdapter instance."""
    return BuilderSkillAdapter(
        generate_code_use_case=mock_generate_code_use_case,
        generate_tests_use_case=mock_generate_tests_use_case,
    )


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
def sample_code_file():
    """Create sample CodeFile."""
    return CodeFile(
        path="generated_code_abc123.py",
        content="def add(a, b):\n    return a + b",
        metadata={"source": "llm_generation"},
    )


@pytest.fixture
def sample_test_cases():
    """Create sample TestCase list."""
    return [
        TestCase(
            name="test_add",
            code="def test_add():\n    assert add(2, 3) == 5",
        ),
        TestCase(
            name="test_add_negative",
            code="def test_add_negative():\n    assert add(-1, 1) == 0",
        ),
    ]


@pytest.mark.asyncio
async def test_execute_calls_generate_code_and_tests(
    builder_adapter,
    mock_generate_code_use_case,
    mock_generate_tests_use_case,
    sample_memory_snapshot,
    sample_code_file,
    sample_test_cases,
):
    """Test execute calls GenerateCodeUseCase and GenerateTestsUseCase."""
    # Setup mocks
    mock_generate_code_use_case.generate_code.return_value = sample_code_file
    mock_generate_tests_use_case.generate_tests.return_value = sample_test_cases

    # Execute
    input_data = {
        "requirements": "Create add function",
        "test_cases": [{"name": "test_add", "code": "def test_add(): ..."}],
    }
    result = await builder_adapter.execute(input_data, sample_memory_snapshot)

    # Verify
    assert result.status == SkillResultStatus.SUCCESS
    assert result.output is not None
    assert "code" in result.output
    assert "tests" in result.output
    mock_generate_code_use_case.generate_code.assert_called_once()
    mock_generate_tests_use_case.generate_tests.assert_called_once()


@pytest.mark.asyncio
async def test_execute_handles_generate_code_error(
    builder_adapter,
    mock_generate_code_use_case,
    mock_generate_tests_use_case,
    sample_memory_snapshot,
):
    """Test execute handles GenerateCodeUseCase errors."""
    # Setup mock to raise error
    mock_generate_code_use_case.generate_code.side_effect = Exception(
        "Code generation error"
    )

    # Execute
    input_data = {
        "requirements": "Create add function",
        "test_cases": [],
    }
    result = await builder_adapter.execute(input_data, sample_memory_snapshot)

    # Should return failure result
    assert result.status == SkillResultStatus.FAILURE
    assert result.error is not None
    assert "error" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_handles_generate_tests_error(
    builder_adapter,
    mock_generate_code_use_case,
    mock_generate_tests_use_case,
    sample_memory_snapshot,
    sample_code_file,
):
    """Test execute handles GenerateTestsUseCase errors."""
    # Setup mocks
    mock_generate_code_use_case.generate_code.return_value = sample_code_file
    mock_generate_tests_use_case.generate_tests.side_effect = Exception(
        "Test generation error"
    )

    # Execute
    input_data = {
        "requirements": "Create add function",
        "test_cases": [],
    }
    result = await builder_adapter.execute(input_data, sample_memory_snapshot)

    # Should return failure result
    assert result.status == SkillResultStatus.FAILURE
    assert result.error is not None
    assert "error" in result.error.lower()


@pytest.mark.asyncio
async def test_get_skill_id_returns_builder(
    builder_adapter,
):
    """Test get_skill_id returns builder."""
    skill_id = builder_adapter.get_skill_id()

    assert skill_id == SkillType.BUILDER.value


@pytest.mark.asyncio
async def test_execute_creates_test_cases_correctly(
    builder_adapter,
    mock_generate_code_use_case,
    mock_generate_tests_use_case,
    sample_memory_snapshot,
    sample_code_file,
    sample_test_cases,
):
    """Test execute creates TestCase entities correctly."""
    mock_generate_code_use_case.generate_code.return_value = sample_code_file
    mock_generate_tests_use_case.generate_tests.return_value = sample_test_cases

    input_data = {
        "requirements": "Create add function",
        "test_cases": [
            {"name": "test_add", "code": "def test_add(): assert add(2, 3) == 5"}
        ],
    }
    await builder_adapter.execute(input_data, sample_memory_snapshot)

    # Verify TestCase entities were created correctly
    call_args = mock_generate_code_use_case.generate_code.call_args
    assert call_args is not None
    test_cases_arg = call_args[1]["test_cases"]
    assert len(test_cases_arg) == 1
    assert isinstance(test_cases_arg[0], TestCase)
    assert test_cases_arg[0].name == "test_add"
