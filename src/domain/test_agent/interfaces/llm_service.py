"""Protocol for test agent LLM services."""

from typing import Protocol


class ITestAgentLLMService(Protocol):
    """Protocol for test agent LLM services.

    Purpose:
        Defines the interface for LLM services used by test agent.
        Infrastructure layer implementations must conform to this protocol.

    Methods:
        generate_tests_prompt: Generate prompt for test generation
        generate_code_prompt: Generate prompt for code generation
    """

    def generate_tests_prompt(self, code: str) -> str:
        """Generate prompt for test generation.

        Args:
            code: Source code to generate tests for.

        Returns:
            Formatted prompt string for LLM.
        """
        ...

    def generate_code_prompt(
        self, requirements: str, tests: str, source_code: str = ""
    ) -> str:
        """Generate prompt for code generation.

        Args:
            requirements: Requirements description.
            tests: Test cases as string.

        Returns:
            Formatted prompt string for LLM.
        """
        ...
