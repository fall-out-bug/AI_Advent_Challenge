"""Protocol for coverage aggregation services."""

from typing import Protocol

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestResult


class ICoverageAggregator(Protocol):
    """Protocol for coverage aggregation services.

    Purpose:
        Defines the interface for aggregating test coverage across multiple
        test results and identifying coverage gaps.

    Methods:
        aggregate_coverage: Aggregate coverage from multiple test results
        identify_gaps: Identify uncovered lines and functions
    """

    def aggregate_coverage(self, test_results: list[TestResult]) -> float:
        """Aggregate coverage from multiple test results.

        Purpose:
            Combines coverage percentages from multiple test results,
            handling overlapping coverage and deduplication.

        Args:
            test_results: List of TestResult entities with coverage data.

        Returns:
            Aggregated coverage percentage (0.0-100.0).

        Raises:
            ValueError: If test_results is empty or invalid.
        """
        ...

    def identify_gaps(self, coverage: float, code_file: CodeFile) -> list[str]:
        """Identify uncovered lines and functions.

        Purpose:
            Analyzes code file to identify what is not covered by tests,
            returning a list of gap descriptions.

        Args:
            coverage: Current coverage percentage (0.0-100.0).
            code_file: CodeFile entity to analyze.

        Returns:
            List of gap descriptions (e.g., ["line 42", "function calculate_total"]).

        Raises:
            ValueError: If coverage is invalid or code_file is empty.
        """
        ...
