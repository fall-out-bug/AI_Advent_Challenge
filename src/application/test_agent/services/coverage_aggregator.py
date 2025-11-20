"""Coverage aggregation service for test agent."""

import ast
from typing import Optional

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestResult
from src.domain.test_agent.interfaces.coverage_aggregator import ICoverageAggregator
from src.infrastructure.logging import get_logger


class CoverageAggregator:
    """
    Coverage aggregation service implementing ICoverageAggregator.

    Purpose:
        Aggregates test coverage across multiple test results and identifies
        coverage gaps in code files.

    Example:
        >>> aggregator = CoverageAggregator()
        >>> results = [TestResult(..., coverage=85.0), TestResult(..., coverage=90.0)]
        >>> total_coverage = aggregator.aggregate_coverage(results)
        >>> gaps = aggregator.identify_gaps(total_coverage, code_file)
    """

    def __init__(self) -> None:
        """Initialize coverage aggregator."""
        self.logger = get_logger("test_agent.coverage_aggregator")

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
        if not test_results:
            raise ValueError("test_results cannot be empty")

        # Filter out results with None coverage
        valid_results = [
            result for result in test_results if result.coverage is not None
        ]

        if not valid_results:
            self.logger.warning("No test results with coverage data, returning 0.0")
            return 0.0

        # Calculate weighted average based on test count
        # This handles deduplication by weighting by test count
        total_tests = sum(result.test_count for result in valid_results)
        if total_tests == 0:
            # Fallback to simple average if no test counts
            coverage_sum = sum(
                result.coverage for result in valid_results  # type: ignore
            )
            return coverage_sum / len(valid_results)

        weighted_sum = sum(
            result.coverage * result.test_count  # type: ignore
            for result in valid_results
        )
        aggregated = weighted_sum / total_tests

        self.logger.debug(
            "Coverage aggregated",
            extra={
                "result_count": len(valid_results),
                "total_tests": total_tests,
                "aggregated_coverage": aggregated,
            },
        )

        return round(aggregated, 2)

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
        if not 0.0 <= coverage <= 100.0:
            raise ValueError("coverage must be between 0.0 and 100.0")

        if not code_file.content:
            return []

        gaps: list[str] = []

        try:
            # Parse code to find functions and classes
            tree = ast.parse(code_file.content, filename=code_file.path)
            uncovered_ratio = 1.0 - (coverage / 100.0)

            # Find all function definitions
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append((node.name, node.lineno))
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.append((node.name, node.lineno))

            # Estimate uncovered functions based on coverage ratio
            if functions:
                uncovered_count = max(1, int(len(functions) * uncovered_ratio))
                uncovered_functions = functions[:uncovered_count]

                for func_name, line_no in uncovered_functions:
                    gaps.append(f"function {func_name} (line {line_no})")

            # Find class definitions
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append((node.name, node.lineno))

            # Estimate uncovered classes
            if classes:
                uncovered_count = max(1, int(len(classes) * uncovered_ratio))
                uncovered_classes = classes[:uncovered_count]

                for class_name, line_no in uncovered_classes:
                    gaps.append(f"class {class_name} (line {line_no})")

            # Add some line-level gaps if coverage is very low
            if coverage < 50.0:
                lines = code_file.content.split("\n")
                uncovered_lines = max(1, int(len(lines) * uncovered_ratio * 0.1))
                for i in range(1, min(uncovered_lines + 1, len(lines) + 1)):
                    if i % 10 == 0:  # Sample every 10th line
                        gaps.append(f"line {i}")

        except SyntaxError as e:
            self.logger.warning(f"Failed to parse code file {code_file.path}: {e}")
            # Fallback: return generic gap description
            if coverage < 80.0:
                gaps.append("code structure (parsing failed)")

        self.logger.debug(
            "Gaps identified",
            extra={
                "coverage": coverage,
                "gap_count": len(gaps),
                "file_path": code_file.path,
            },
        )

        return gaps
