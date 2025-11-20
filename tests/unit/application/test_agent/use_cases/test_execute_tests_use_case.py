"""Unit tests for ExecuteTestsUseCase."""

from unittest.mock import MagicMock

import pytest

from src.application.test_agent.use_cases.execute_tests_use_case import (
    ExecuteTestsUseCase,
)
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.entities.test_result import TestResult, TestStatus


@pytest.fixture
def mock_test_executor():
    """Create mock test executor."""
    executor = MagicMock()
    executor.execute = MagicMock(
        return_value=TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=85.5,
        )
    )
    executor.get_coverage = MagicMock(return_value=85.5)
    return executor


@pytest.fixture
def sample_test_cases():
    """Create sample test cases."""
    return [
        TestCase(
            name="test_example",
            code="def test_example(): assert True",
        )
    ]


@pytest.fixture
def sample_code_file():
    """Create sample code file."""
    return CodeFile(
        path="test.py",
        content="def calculate(a, b): return a + b",
    )


def test_execute_tests_returns_test_result(
    mock_test_executor, sample_test_cases, sample_code_file
):
    """Test execute_tests returns test result."""
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)

    result = use_case.execute_tests(sample_test_cases, sample_code_file)

    assert isinstance(result, TestResult)
    assert result.status == TestStatus.PASSED


def test_execute_tests_uses_test_executor(
    mock_test_executor, sample_test_cases, sample_code_file
):
    """Test execute_tests uses test executor."""
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)

    use_case.execute_tests(sample_test_cases, sample_code_file)

    mock_test_executor.execute.assert_called_once()


def test_execute_tests_collects_coverage(
    mock_test_executor, sample_test_cases, sample_code_file
):
    """Test execute_tests collects coverage."""
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)

    result = use_case.execute_tests(sample_test_cases, sample_code_file)

    assert result.coverage == 85.5
    mock_test_executor.get_coverage.assert_called_once()


def test_execute_tests_handles_execution_errors(
    mock_test_executor, sample_test_cases, sample_code_file
):
    """Test execute_tests handles execution errors."""
    mock_test_executor.execute = MagicMock(side_effect=Exception("Execution error"))
    use_case = ExecuteTestsUseCase(test_executor=mock_test_executor)

    with pytest.raises(Exception, match="Execution error"):
        use_case.execute_tests(sample_test_cases, sample_code_file)
