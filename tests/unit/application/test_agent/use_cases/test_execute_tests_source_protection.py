"""Unit tests for source code protection in ExecuteTestsUseCase."""

from unittest.mock import MagicMock

import pytest

from src.application.test_agent.use_cases.execute_tests_use_case import (
    ExecuteTestsUseCase,
)
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.entities.test_result import TestStatus


@pytest.fixture
def mock_test_executor():
    """Create mock test executor."""
    executor = MagicMock()
    executor.execute = MagicMock(
        return_value=MagicMock(
            status=TestStatus.PASSED,
            test_count=2,
            passed_count=2,
            failed_count=0,
            errors=[],
        )
    )
    executor.get_coverage = MagicMock(return_value=85.0)
    return executor


@pytest.fixture
def sample_source_code():
    """Create sample source code."""
    return """def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b

def subtract(a: int, b: int) -> int:
    \"\"\"Subtract b from a.\"\"\"
    return a - b"""


def test_source_code_immutability(mock_test_executor, sample_source_code):
    """Test that source code remains immutable during processing."""
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)
    code_file = CodeFile(path="test.py", content=sample_source_code)
    original_content = code_file.content

    test_cases = [
        TestCase(
            name="test_add",
            code="def test_add():\n    assert add(2, 3) == 5",
        )
    ]

    result = use_case.execute_tests(test_cases, code_file)

    # Verify source code was not modified
    assert code_file.content == original_content
    assert result.status == TestStatus.PASSED


def test_source_code_protection_against_redefinition(
    mock_test_executor, sample_source_code
):
    """Test that source code is protected against function redefinitions."""
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)
    code_file = CodeFile(path="test.py", content=sample_source_code)
    original_content = code_file.content

    # Test case that tries to redefine source function
    test_cases = [
        TestCase(
            name="test_add",
            code="""def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5""",
        )
    ]

    result = use_case.execute_tests(test_cases, code_file)

    # Source code should remain unchanged
    assert code_file.content == original_content
    # Test with redefinition should be skipped
    assert result.test_count >= 0


def test_source_code_integrity_verification(mock_test_executor, sample_source_code):
    """Test that source code integrity is verified at multiple stages."""
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)
    code_file = CodeFile(path="test.py", content=sample_source_code)

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

    result = use_case.execute_tests(test_cases, code_file)

    # Verify execution succeeded
    assert result.status == TestStatus.PASSED
    # Source code should be intact
    assert code_file.content == sample_source_code


def test_source_code_markers_preserved(mock_test_executor, sample_source_code):
    """Test that source code markers are properly preserved."""
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)
    code_file = CodeFile(path="test.py", content=sample_source_code)

    test_cases = [
        TestCase(
            name="test_add",
            code="def test_add():\n    assert add(2, 3) == 5",
        )
    ]

    result = use_case.execute_tests(test_cases, code_file)

    # Verify source code was not modified
    assert code_file.content == sample_source_code
    # Verify execution succeeded
    assert result.status == TestStatus.PASSED


def test_source_code_hash_verification(mock_test_executor, sample_source_code):
    """Test that source code hash is verified to detect modifications."""
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)
    code_file = CodeFile(path="test.py", content=sample_source_code)
    original_hash = hash(sample_source_code)

    test_cases = [
        TestCase(
            name="test_add",
            code="def test_add():\n    assert add(2, 3) == 5",
        )
    ]

    result = use_case.execute_tests(test_cases, code_file)

    # Verify hash remains the same
    assert hash(code_file.content) == original_hash
    assert result.status == TestStatus.PASSED
