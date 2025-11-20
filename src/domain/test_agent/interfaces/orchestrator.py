"""Protocol for test agent orchestrator."""

from typing import Protocol

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_result import TestResult


class ITestAgentOrchestrator(Protocol):
    """Protocol for test agent orchestrator.

    Purpose:
        Defines the interface for orchestrating test agent workflow.

    Methods:
        orchestrate_test_workflow: Orchestrate complete test workflow
    """

    async def orchestrate_test_workflow(self, code_file: CodeFile) -> TestResult:
        """Orchestrate complete test workflow.

        Args:
            code_file: CodeFile domain entity to process.

        Returns:
            TestResult domain entity with workflow results.

        Raises:
            Exception: If workflow execution fails.
        """
        ...
