"""Unit tests for TestResultReporter."""

import pytest

from src.domain.test_agent.entities.test_result import TestResult, TestStatus
from src.infrastructure.test_agent.reporting.test_result_reporter import (
    TestResultReporter,
)


def test_report_returns_formatted_string():
    """Test report returns formatted string."""
    reporter = TestResultReporter()
    result = TestResult(
        status=TestStatus.PASSED,
        test_count=10,
        passed_count=10,
        failed_count=0,
        coverage=85.5,
    )

    report = reporter.report(result)

    assert isinstance(report, str)
    assert "PASSED" in report or "passed" in report
    assert "10" in report


def test_report_coverage_returns_formatted_string():
    """Test report_coverage returns formatted string."""
    reporter = TestResultReporter()
    coverage = 85.5

    report = reporter.report_coverage(coverage)

    assert isinstance(report, str)
    assert "85.5" in report or "85" in report
    assert "%" in report or "coverage" in report.lower()


def test_report_handles_errors():
    """Test report handles errors."""
    reporter = TestResultReporter()
    result = TestResult(
        status=TestStatus.FAILED,
        test_count=5,
        passed_count=3,
        failed_count=2,
        errors=["AssertionError: expected 3, got 2"],
    )

    report = reporter.report(result)

    assert isinstance(report, str)
    assert "FAILED" in report or "failed" in report
    assert "2" in report


def test_report_includes_all_metrics():
    """Test report includes all metrics."""
    reporter = TestResultReporter()
    result = TestResult(
        status=TestStatus.PASSED,
        test_count=15,
        passed_count=15,
        failed_count=0,
        coverage=92.3,
    )

    report = reporter.report(result)

    assert isinstance(report, str)
    assert "15" in report
    assert "92" in report or "92.3" in report
