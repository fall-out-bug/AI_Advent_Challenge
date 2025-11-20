"""Unit tests for TestResult entity."""

import pytest

from src.domain.test_agent.entities.test_result import TestResult, TestStatus


def test_test_result_creation_with_status():
    """Test TestResult creation with status."""
    test_result = TestResult(
        status=TestStatus.PASSED,
        test_count=5,
        passed_count=5,
        failed_count=0,
    )

    assert test_result.status == TestStatus.PASSED
    assert test_result.test_count == 5
    assert test_result.passed_count == 5
    assert test_result.failed_count == 0
    assert test_result.coverage is None
    assert test_result.errors == []


def test_test_result_with_coverage():
    """Test TestResult with coverage."""
    test_result = TestResult(
        status=TestStatus.PASSED,
        test_count=10,
        passed_count=10,
        failed_count=0,
        coverage=85.5,
    )

    assert test_result.coverage == 85.5
    assert test_result.status == TestStatus.PASSED


def test_test_result_with_errors():
    """Test TestResult with errors."""
    errors = ["AssertionError: expected 3, got 2", "SyntaxError: invalid syntax"]
    test_result = TestResult(
        status=TestStatus.FAILED,
        test_count=5,
        passed_count=3,
        failed_count=2,
        errors=errors,
    )

    assert test_result.status == TestStatus.FAILED
    assert test_result.errors == errors
    assert len(test_result.errors) == 2


def test_test_result_validation():
    """Test TestResult validation errors."""
    with pytest.raises(ValueError, match="test_count cannot be negative"):
        TestResult(
            status=TestStatus.PASSED,
            test_count=-1,
            passed_count=0,
            failed_count=0,
        )

    with pytest.raises(ValueError, match="passed_count cannot be negative"):
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=-1,
            failed_count=0,
        )

    with pytest.raises(ValueError, match="failed_count cannot be negative"):
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=-1,
        )

    with pytest.raises(ValueError, match="coverage must be between 0 and 100"):
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=150.0,
        )
