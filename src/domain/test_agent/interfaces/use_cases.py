"""Protocols for test agent use cases."""

from typing import Protocol

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.entities.test_result import TestResult


class IGenerateTestsUseCase(Protocol):
    """Protocol for test generation use case.

    Purpose:
        Defines the interface for generating test cases from code.

    Methods:
        generate_tests: Generate test cases from code file
    """

    async def generate_tests(self, code_file: CodeFile) -> list[TestCase]:
        """Generate test cases from code file.

        Args:
            code_file: CodeFile domain entity with code to test.

        Returns:
            List of TestCase domain entities.

        Raises:
            Exception: If test generation fails.
        """
        ...


class IGenerateCodeUseCase(Protocol):
    """Protocol for code generation use case.

    Purpose:
        Defines the interface for generating code from requirements and tests.

    Methods:
        generate_code: Generate code from requirements and test cases
    """

    async def generate_code(
        self,
        requirements: str,
        test_cases: list[TestCase],
        source_code: str = "",
    ) -> CodeFile:
        """Generate code from requirements and test cases.

        Args:
            requirements: Requirements description.
            test_cases: List of TestCase domain entities.
            source_code: Optional source code for reference (to match structure).

        Returns:
            CodeFile domain entity with generated code.

        Raises:
            Exception: If code generation fails.
        """
        ...


class IExecuteTestsUseCase(Protocol):
    """Protocol for test execution use case.

    Purpose:
        Defines the interface for executing tests and collecting results.

    Methods:
        execute_tests: Execute tests and return results
    """

    def execute_tests(
        self, test_cases: list[TestCase], code_file: CodeFile
    ) -> TestResult:
        """Execute tests and return results.

        Args:
            test_cases: List of TestCase domain entities to execute.
            code_file: CodeFile domain entity with code to test.

        Returns:
            TestResult domain entity with execution results.

        Raises:
            Exception: If test execution fails.
        """
        ...
