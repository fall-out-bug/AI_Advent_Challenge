"""Unit tests for TestExecutor (pytest adapter)."""

from unittest.mock import MagicMock, patch

import pytest

from src.domain.test_agent.entities.test_result import TestResult, TestStatus
from src.infrastructure.test_agent.adapters.pytest_executor import TestExecutor


def test_execute_tests_with_valid_file(tmp_path):
    """Test execute tests with valid file."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_example(): assert True")

    executor = TestExecutor()
    result = executor.execute(str(test_file))

    assert isinstance(result, TestResult)
    assert result.status == TestStatus.PASSED
    assert result.test_count > 0
    assert result.passed_count > 0


def test_execute_tests_with_failing_tests(tmp_path):
    """Test execute tests with failing tests."""
    test_file = tmp_path / "test_failing.py"
    test_file.write_text("def test_failing(): assert False")

    executor = TestExecutor()
    result = executor.execute(str(test_file))

    assert isinstance(result, TestResult)
    assert result.status == TestStatus.FAILED
    assert result.failed_count > 0
    assert len(result.errors) > 0


def test_get_coverage_returns_float(tmp_path):
    """Test get_coverage returns float."""
    test_file = tmp_path / "test_coverage.py"
    test_file.write_text("def test_coverage(): assert True")

    executor = TestExecutor()
    coverage = executor.get_coverage(str(test_file))

    assert isinstance(coverage, float)
    assert 0.0 <= coverage <= 100.0


def test_execute_handles_missing_file():
    """Test execute handles missing file."""
    executor = TestExecutor()

    with pytest.raises(FileNotFoundError):
        executor.execute("nonexistent_file.py")


def test_execute_handles_syntax_errors(tmp_path):
    """Test execute handles syntax errors."""
    test_file = tmp_path / "test_syntax_error.py"
    test_file.write_text("def test_syntax_error(:  # syntax error")

    executor = TestExecutor()
    result = executor.execute(str(test_file))

    assert isinstance(result, TestResult)
    # Pytest returns FAILED for syntax errors during collection
    assert result.status in (TestStatus.FAILED, TestStatus.ERROR)
    assert len(result.errors) > 0 or result.failed_count > 0
