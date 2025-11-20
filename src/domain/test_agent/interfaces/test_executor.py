"""Protocol for test executors."""

from typing import Protocol

from src.domain.test_agent.entities.test_result import TestResult


class ITestExecutor(Protocol):
    """Protocol for test executors.

    Purpose:
        Defines the interface for test execution adapters.
        Infrastructure layer implementations must conform to this protocol.

    Methods:
        execute: Execute tests and return results
        get_coverage: Get test coverage percentage
    """

    def execute(self, test_file_path: str) -> TestResult:
        """Execute tests and return results.

        Args:
            test_file_path: Path to the test file to execute.

        Returns:
            TestResult domain entity with execution results.

        Raises:
            Exception: If test execution fails.
        """
        ...

    def get_coverage(self, test_file_path: str) -> float:
        """Get test coverage percentage.

        Args:
            test_file_path: Path to the test file.

        Returns:
            Coverage percentage as float (0.0-100.0).

        Raises:
            Exception: If coverage calculation fails.
        """
        ...
