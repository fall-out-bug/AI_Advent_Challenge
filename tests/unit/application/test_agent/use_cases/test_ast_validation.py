"""Unit tests for enhanced AST-based validation."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.test_agent.use_cases.generate_tests_use_case import (
    GenerateTestsUseCase,
)
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = MagicMock()
    service.generate_tests_prompt = MagicMock(
        return_value="Generate tests for: def add(a, b): return a + b"
    )
    return service


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = AsyncMock()
    client.generate = AsyncMock(return_value="def test_add(): assert add(2, 3) == 5")
    return client


@pytest.fixture
def sample_code_file():
    """Create sample code file."""
    return CodeFile(
        path="test.py",
        content="def add(a: int, b: int) -> int:\n    return a + b",
    )


def test_is_valid_test_code_with_valid_test(mock_llm_service, mock_llm_client):
    """Test _is_valid_test_code with valid test code."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    source_function_names = {"add", "subtract"}

    valid_code = "def test_add():\n    assert add(2, 3) == 5"
    result = use_case._is_valid_test_code(valid_code, source_function_names)

    assert result is True


def test_is_valid_test_code_with_redefinition(mock_llm_service, mock_llm_client):
    """Test _is_valid_test_code detects function redefinition."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    source_function_names = {"add", "subtract"}

    invalid_code = """def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5"""
    result = use_case._is_valid_test_code(invalid_code, source_function_names)

    assert result is False


def test_is_valid_test_code_with_async_function(mock_llm_service, mock_llm_client):
    """Test _is_valid_test_code handles async functions."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    source_function_names = {"add"}

    valid_code = "async def test_add():\n    assert add(2, 3) == 5"
    result = use_case._is_valid_test_code(valid_code, source_function_names)

    assert result is True


def test_is_valid_test_code_with_non_test_function(mock_llm_service, mock_llm_client):
    """Test _is_valid_test_code rejects non-test functions."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    source_function_names = {"add"}

    invalid_code = """def helper_function():
    return 42

def test_add():
    assert add(2, 3) == 5"""
    result = use_case._is_valid_test_code(invalid_code, source_function_names)

    assert result is False


def test_is_valid_test_code_with_syntax_error(mock_llm_service, mock_llm_client):
    """Test _is_valid_test_code handles syntax errors."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    source_function_names = {"add"}

    invalid_code = "def test_add():\n    assert add(2, 3) =="  # Incomplete
    result = use_case._is_valid_test_code(invalid_code, source_function_names)

    assert result is False


def test_validate_and_clean_tests_filters_redefinitions(
    mock_llm_service, mock_llm_client, sample_code_file
):
    """Test _validate_and_clean_tests filters out redefinitions."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )

    test_cases = [
        TestCase(
            name="test_add",
            code="def test_add():\n    assert add(2, 3) == 5",
        ),
        TestCase(
            name="test_with_redefinition",
            code="""def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5""",
        ),
    ]

    valid_tests = use_case._validate_and_clean_tests(test_cases, sample_code_file)

    # Enhanced validation should filter out redefinition
    # Either it's filtered out completely, or cleaned to remove redefinition
    assert len(valid_tests) >= 1
    # Verify no redefinitions in valid tests
    for test in valid_tests:
        assert "def add(a, b):" not in test.code or test.code.count("def add") == 0


def test_validate_pytest_syntax_with_valid_tests(mock_llm_service, mock_llm_client):
    """Test _validate_pytest_syntax with valid test cases."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )

    test_cases = [
        TestCase(
            name="test_add",
            code="def test_add():\n    assert add(2, 3) == 5",
        ),
        TestCase(
            name="test_subtract",
            code="def test_subtract():\n    assert subtract(5, 3) == 2",
        ),
    ]

    # Should not raise
    use_case._validate_pytest_syntax(test_cases)


def test_validate_pytest_syntax_with_invalid_syntax(mock_llm_service, mock_llm_client):
    """Test _validate_pytest_syntax raises on invalid syntax."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )

    test_cases = [
        TestCase(
            name="test_invalid",
            code="def test_invalid():\n    assert add(2, 3) ==",  # Incomplete
        )
    ]

    with pytest.raises(ValueError, match="Invalid pytest syntax"):
        use_case._validate_pytest_syntax(test_cases)


def test_validate_pytest_syntax_with_no_test_function(
    mock_llm_service, mock_llm_client
):
    """Test _validate_pytest_syntax rejects non-test functions."""
    use_case = GenerateTestsUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )

    test_cases = [
        TestCase(
            name="not_a_test",
            code="def helper():\n    return 42",
        )
    ]

    with pytest.raises(ValueError, match="does not contain a test function"):
        use_case._validate_pytest_syntax(test_cases)
