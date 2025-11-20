"""Protocol for test result reporters."""

from typing import Protocol

from src.domain.test_agent.entities.test_result import TestResult


class ITestResultReporter(Protocol):
    """Protocol for test result reporters.

    Purpose:
        Defines the interface for test result reporting adapters.
        Infrastructure layer implementations must conform to this protocol.

    Methods:
        report: Format and return test results as string
        report_coverage: Format and return coverage information as string
    """

    def report(self, test_result: TestResult) -> str:
        """Format and return test results as string.

        Args:
            test_result: TestResult domain entity.

        Returns:
            Formatted test results string.
        """
        ...

    def report_coverage(self, coverage: float) -> str:
        """Format and return coverage information as string.

        Args:
            coverage: Coverage percentage (0.0-100.0).

        Returns:
            Formatted coverage string.
        """
        ...
