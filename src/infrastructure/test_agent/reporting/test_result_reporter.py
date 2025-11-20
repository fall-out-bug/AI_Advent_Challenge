"""Test result reporter adapter for formatting results."""

from src.domain.test_agent.entities.test_result import TestResult
from src.domain.test_agent.interfaces.reporter import ITestResultReporter


class TestResultReporter:
    """
    Test result reporter implementing ITestResultReporter.

    Purpose:
        Formats test results and coverage information for display.

    Example:
        >>> reporter = TestResultReporter()
        >>> result = TestResult(...)
        >>> report = reporter.report(result)
    """

    def report(self, test_result: TestResult) -> str:
        """Format and return test results as string.

        Args:
            test_result: TestResult domain entity.

        Returns:
            Formatted test results string.
        """
        lines = [
            f"Test Execution Results: {test_result.status.value.upper()}",
            f"Total Tests: {test_result.test_count}",
            f"Passed: {test_result.passed_count}",
            f"Failed: {test_result.failed_count}",
        ]

        if test_result.coverage is not None:
            lines.append(f"Coverage: {test_result.coverage:.2f}%")

        if test_result.errors:
            lines.append("\nErrors:")
            for error in test_result.errors:
                lines.append(f"  - {error}")

        return "\n".join(lines)

    def report_coverage(self, coverage: float) -> str:
        """Format and return coverage information as string.

        Args:
            coverage: Coverage percentage (0.0-100.0).

        Returns:
            Formatted coverage string.
        """
        return f"Test Coverage: {coverage:.2f}%"
