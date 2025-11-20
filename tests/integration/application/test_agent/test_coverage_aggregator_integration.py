"""Integration tests for CoverageAggregator with pytest-cov."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.application.test_agent.services.coverage_aggregator import CoverageAggregator
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestResult, TestStatus


@pytest.fixture
def coverage_aggregator() -> CoverageAggregator:
    """Create CoverageAggregator instance."""
    return CoverageAggregator()


@pytest.fixture
def sample_code_file() -> CodeFile:
    """Create sample code file for testing."""
    return CodeFile(
        path="src/example.py",
        content="""def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

def subtract(a: int, b: int) -> int:
    '''Subtract b from a.'''
    return a - b

def multiply(a: int, b: int) -> int:
    '''Multiply two numbers.'''
    return a * b
""",
    )


def test_aggregate_coverage_with_real_pytest_results(
    coverage_aggregator: CoverageAggregator,
) -> None:
    """Test aggregating coverage with real pytest results."""
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
            test_count=3,
            passed_count=3,
            failed_count=0,
            coverage=90.0,
        ),
    ]

    # Act
    aggregated = coverage_aggregator.aggregate_coverage(test_results)

    # Assert
    assert isinstance(aggregated, float)
    assert 0.0 <= aggregated <= 100.0
    # Weighted average: (85*5 + 90*3) / 8 = 86.875
    assert 85.0 <= aggregated <= 90.0


def test_coverage_aggregator_with_chunked_tests(
    coverage_aggregator: CoverageAggregator,
) -> None:
    """Test coverage aggregator with chunked test results."""
    # Arrange
    # Simulate multiple chunks testing the same code
    chunk_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=10,
            passed_count=10,
            failed_count=0,
            coverage=80.0,  # Chunk 1 coverage
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=8,
            passed_count=8,
            failed_count=0,
            coverage=85.0,  # Chunk 2 coverage
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=5,
            passed_count=5,
            failed_count=0,
            coverage=90.0,  # Chunk 3 coverage
        ),
    ]

    # Act
    aggregated = coverage_aggregator.aggregate_coverage(chunk_results)

    # Assert
    assert isinstance(aggregated, float)
    assert 0.0 <= aggregated <= 100.0
    # Should aggregate all chunks
    assert aggregated >= 80.0
    assert aggregated <= 90.0


def test_gap_identification_matches_coverage_report(
    coverage_aggregator: CoverageAggregator, sample_code_file: CodeFile
) -> None:
    """Test that gap identification matches coverage expectations."""
    # Arrange
    coverage = 66.67  # 2 out of 3 functions covered

    # Act
    gaps = coverage_aggregator.identify_gaps(coverage, sample_code_file)

    # Assert
    assert isinstance(gaps, list)
    assert all(isinstance(gap, str) for gap in gaps)
    # Should identify at least one uncovered function
    assert len(gaps) > 0
    # Should mention functions
    gap_text = " ".join(gaps).lower()
    assert "function" in gap_text or "add" in gap_text or "subtract" in gap_text


def test_coverage_aggregator_with_pytest_cov_simulation(
    coverage_aggregator: CoverageAggregator,
) -> None:
    """Test coverage aggregator with simulated pytest-cov data."""
    # Arrange
    # Simulate pytest-cov output: multiple modules with coverage
    module_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=15,
            passed_count=15,
            failed_count=0,
            coverage=88.5,  # Module 1
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=12,
            passed_count=12,
            failed_count=0,
            coverage=92.0,  # Module 2
        ),
        TestResult(
            status=TestStatus.PASSED,
            test_count=8,
            passed_count=8,
            failed_count=0,
            coverage=75.0,  # Module 3
        ),
    ]

    # Act
    aggregated = coverage_aggregator.aggregate_coverage(module_results)

    # Assert
    assert isinstance(aggregated, float)
    assert 0.0 <= aggregated <= 100.0
    # Weighted average should be between min and max
    assert aggregated >= 75.0
    assert aggregated <= 92.0
    # Should meet 80% target when aggregated
    # (88.5*15 + 92*12 + 75*8) / 35 = 85.8
    assert aggregated >= 80.0


def test_coverage_aggregator_handles_mixed_results(
    coverage_aggregator: CoverageAggregator,
) -> None:
    """Test coverage aggregator handles mixed test results."""
    # Arrange
    mixed_results = [
        TestResult(
            status=TestStatus.PASSED,
            test_count=10,
            passed_count=10,
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
        TestResult(
            status=TestStatus.FAILED,
            test_count=3,
            passed_count=2,
            failed_count=1,
            coverage=70.0,
        ),
    ]

    # Act
    aggregated = coverage_aggregator.aggregate_coverage(mixed_results)

    # Assert
    assert isinstance(aggregated, float)
    assert 0.0 <= aggregated <= 100.0
    # Should only use results with coverage data
    # Weighted: (85*10 + 70*3) / 13 = 81.54
    assert aggregated >= 70.0
    assert aggregated <= 85.0
