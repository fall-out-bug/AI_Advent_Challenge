"""Test agent orchestrator for coordinating workflow."""

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.entities.test_result import TestResult
from src.domain.test_agent.interfaces.orchestrator import ITestAgentOrchestrator
from src.domain.test_agent.interfaces.use_cases import (
    IExecuteTestsUseCase,
    IGenerateCodeUseCase,
    IGenerateTestsUseCase,
)


class TestAgentOrchestrator:
    """
    Test agent orchestrator implementing ITestAgentOrchestrator.

    Purpose:
        Orchestrates the complete test agent workflow: test generation,
        code generation, test execution, and result reporting.

    Example:
        >>> orchestrator = TestAgentOrchestrator(
        ...     generate_tests_use_case=gen_tests,
        ...     generate_code_use_case=gen_code,
        ...     execute_tests_use_case=exec_tests,
        ... )
        >>> code_file = CodeFile(path="test.py", content="...")
        >>> result = await orchestrator.orchestrate_test_workflow(code_file)
        >>> result.status
        <TestStatus.PASSED: 'passed'>
    """

    def __init__(
        self,
        generate_tests_use_case: IGenerateTestsUseCase,
        generate_code_use_case: IGenerateCodeUseCase,
        execute_tests_use_case: IExecuteTestsUseCase,
    ) -> None:
        """Initialize orchestrator.

        Args:
            generate_tests_use_case: Use case for generating tests.
            generate_code_use_case: Use case for generating code.
            execute_tests_use_case: Use case for executing tests.
        """
        self.generate_tests_use_case = generate_tests_use_case
        self.generate_code_use_case = generate_code_use_case
        self.execute_tests_use_case = execute_tests_use_case
        self.generated_code: CodeFile | None = None
        self.generated_test_cases: list[TestCase] = []

    async def orchestrate_test_workflow(self, code_file: CodeFile) -> TestResult:
        """Orchestrate complete test workflow.

        Args:
            code_file: CodeFile domain entity to process.

        Returns:
            TestResult domain entity with workflow results.

        Raises:
            Exception: If any step in workflow fails.
        """
        try:
            test_cases = await self.generate_tests_use_case.generate_tests(code_file)
            # Store generated test cases for CLI access
            self.generated_test_cases = test_cases

            requirements = code_file.metadata.get("requirements", "")
            generated_code = await self.generate_code_use_case.generate_code(
                requirements, test_cases, source_code=code_file.content
            )
            # Store generated code for CLI access
            self.generated_code = generated_code

            result = self.execute_tests_use_case.execute_tests(
                test_cases, generated_code
            )

            return result
        except Exception as e:
            raise Exception(f"Workflow orchestration failed: {e}") from e
