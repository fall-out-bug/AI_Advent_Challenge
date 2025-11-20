"""Unit tests for CoverageAggregator service."""

import pytest

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestResult, TestStatus
from src.domain.test_agent.interfaces.coverage_aggregator import ICoverageAggregator


@pytest.fixture
def coverage_aggregator() -> ICoverageAggregator:
    """Create CoverageAggregator instance.

    Note: This will fail until CoverageAggregator is implemented.
    """
    from src.application.test_agent.services.coverage_aggregator import (
        CoverageAggregator,
    )

    return CoverageAggregator()


def test_aggregate_coverage_single_test_result(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test aggregating coverage from a single test result."""
    # Arrange
    test_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=10,
            passed_count=10,
            failed_count=0,
            coverage=85.5,
        )
    ]

    # Act
    result = coverage_aggregator.aggregate_coverage(test_results)

    # Assert
    assert isinstance(result, float)
    assert 0.0 <= result <= 100.0
    assert result == 85.5


def test_aggregate_coverage_multiple_test_results(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test aggregating coverage from multiple test results."""
    # Arrange
    test_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=80.0,
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=90.0,
        ),
    ]

    # Act
    result = coverage_aggregator.aggregate_coverage(test_results)

    # Assert
    assert isinstance(result, float)
    assert 0.0 <= result <= 100.0
    # Should be average or weighted average
    assert result >= 80.0
    assert result <= 90.0


def test_aggregate_coverage_meets_80_percent_target(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test that aggregated coverage meets 80% target."""
    # Arrange
    test_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=10,
            passed_count=10,
            failed_count=0,
            coverage=85.0,
        )
    ]

    # Act
    result = coverage_aggregator.aggregate_coverage(test_results)

    # Assert
    assert result >= 80.0


def test_aggregate_coverage_below_target(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test aggregating coverage below 80% target."""
    # Arrange
    test_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=10,
            passed_count=10,
            failed_count=0,
            coverage=75.0,
        )
    ]

    # Act
    result = coverage_aggregator.aggregate_coverage(test_results)

    # Assert
    assert isinstance(result, float)
    assert result < 80.0
    assert result == 75.0


def test_identify_gaps_returns_uncovered_lines(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test that identify_gaps returns uncovered lines."""
    # Arrange
    code_file = CodeFile(
        path="src/example.py",
        content="""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""",
    )
    coverage = 50.0  # 50% coverage

    # Act
    gaps = coverage_aggregator.identify_gaps(coverage, code_file)

    # Assert
    assert isinstance(gaps, list)
    assert all(isinstance(gap, str) for gap in gaps)
    # Should identify some uncovered items
    assert len(gaps) > 0


def test_identify_gaps_returns_uncovered_functions(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test that identify_gaps returns uncovered functions."""
    # Arrange
    code_file = CodeFile(
        path="src/example.py",
        content="""def calculate_total(items):
    return sum(items)

def calculate_average(items):
    return sum(items) / len(items)
""",
    )
    coverage = 50.0  # 50% coverage

    # Act
    gaps = coverage_aggregator.identify_gaps(coverage, code_file)

    # Assert
    assert isinstance(gaps, list)
    # Should identify uncovered functions
    assert any("calculate" in gap.lower() or "function" in gap.lower() for gap in gaps)


def test_deduplication_of_overlapping_tests(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test that overlapping test coverage is deduplicated."""
    # Arrange
    # Two test results covering the same code (overlapping)
    test_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=80.0,  # Covers lines 1-10
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=80.0,  # Also covers lines 1-10 (overlap)
        ),
    ]

    # Act
    result = coverage_aggregator.aggregate_coverage(test_results)

    # Assert
    assert isinstance(result, float)
    # Should not double-count overlapping coverage
    # Result should be <= 100.0 and <= max individual coverage
    assert result <= 100.0
    assert result <= 80.0  # Should not exceed individual coverage


def test_aggregate_coverage_with_none_coverage(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test aggregating coverage when some results have None coverage."""
    # Arrange
    test_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=85.0,
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=None,  # No coverage data
        ),
    ]

    # Act
    result = coverage_aggregator.aggregate_coverage(test_results)

    # Assert
    assert isinstance(result, float)
    # Should handle None gracefully (use available coverage)
    assert 0.0 <= result <= 100.0


def test_identify_gaps_with_high_coverage(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test identify_gaps with high coverage (few gaps)."""
    # Arrange
    code_file = CodeFile(
        path="src/example.py",
        content="""def add(a, b):
    return a + b
""",
    )
    coverage = 95.0  # High coverage

    # Act
    gaps = coverage_aggregator.identify_gaps(coverage, code_file)

    # Assert
    assert isinstance(gaps, list)
    # Should have fewer gaps with high coverage
    # (exact count depends on implementation)


def test_identify_gaps_with_empty_code_file(
    coverage_aggregator: ICoverageAggregator,
) -> None:
    """Test identify_gaps with empty code file."""
    # Arrange
    code_file = CodeFile(path="src/empty.py", content="")
    coverage = 0.0

    # Act
    gaps = coverage_aggregator.identify_gaps(coverage, code_file)

    # Assert
    assert isinstance(gaps, list)
    # Empty file should have no gaps or minimal gaps
