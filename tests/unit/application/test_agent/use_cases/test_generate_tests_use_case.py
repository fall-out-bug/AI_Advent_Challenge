"""Unit tests for GenerateTestsUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.test_agent.use_cases.generate_tests_use_case import (
    GenerateTestsUseCase,
)
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = MagicMock()
    service.generate_tests_prompt = MagicMock(
        return_value="Generate tests for this code"
    )
    return service


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = AsyncMock()
    client.generate = AsyncMock(
        return_value="""
def test_example():
    assert True

def test_calculate():
    assert calculate(1, 2) == 3
"""
    )
    return client


async def test_generate_tests_returns_list_of_test_cases(
    mock_llm_service, mock_llm_client
):
    """Test generate_tests returns list of test cases."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    code_file = CodeFile(path="test.py", content="def calculate(a, b): return a + b")

    result = await use_case.generate_tests(code_file)

    assert isinstance(result, list)
    assert all(isinstance(tc, TestCase) for tc in result)
    assert len(result) > 0


async def test_generate_tests_uses_llm_service(mock_llm_service, mock_llm_client):
    """Test generate_tests uses LLM service."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    code_file = CodeFile(path="test.py", content="def add(a, b): return a + b")

    await use_case.generate_tests(code_file)

    mock_llm_service.generate_tests_prompt.assert_called_once()
    assert code_file.content in mock_llm_service.generate_tests_prompt.call_args[0][0]


async def test_generate_tests_validates_pytest_syntax(
    mock_llm_service, mock_llm_client
):
    """Test generate_tests validates pytest syntax."""
    mock_llm_client.generate = AsyncMock(
        return_value="def test_invalid(:  # syntax error"
    )
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    code_file = CodeFile(path="test.py", content="def func(): pass")

    # With multi-pass approach, invalid tests are filtered out
    # If no valid tests remain, ValueError is raised
    with pytest.raises(ValueError, match="No valid test cases could be generated"):
        await use_case.generate_tests(code_file)


async def test_generate_tests_handles_llm_errors(mock_llm_service, mock_llm_client):
    """Test generate_tests handles LLM errors."""
    mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM error"))
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    code_file = CodeFile(path="test.py", content="def func(): pass")

    with pytest.raises(Exception, match="LLM generation failed"):
        await use_case.generate_tests(code_file)


async def test_generate_tests_parses_llm_response(mock_llm_service, mock_llm_client):
    """Test generate_tests parses LLM response."""
    mock_llm_client.generate = AsyncMock(
        return_value="""
def test_function_one():
    assert function_one() == 1

def test_function_two():
    assert function_two() == 2
"""
    )
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    code_file = CodeFile(path="test.py", content="def func(): pass")

    result = await use_case.generate_tests(code_file)

    assert len(result) == 2
    assert result[0].name == "test_function_one"
    assert result[1].name == "test_function_two"
