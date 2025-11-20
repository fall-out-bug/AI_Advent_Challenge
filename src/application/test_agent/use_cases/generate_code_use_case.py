"""Use case for generating code from requirements and tests."""

import ast
import os
import re
from pathlib import Path

from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase
from src.domain.test_agent.interfaces.llm_service import ITestAgentLLMService
from src.domain.test_agent.interfaces.use_cases import IGenerateCodeUseCase
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.logging import get_logger


class GenerateCodeUseCase:
    """
    Use case for generating code based on requirements and test cases.

    Purpose:
        Generates implementation code from requirements and test cases using LLM,
        validates Clean Architecture boundaries, and returns domain entities.

    Example:
        >>> use_case = GenerateCodeUseCase(llm_service=service, llm_client=client)
        >>> test_cases = [TestCase(name="test_add", code="def test_add(): ...")]
        >>> code_file = await use_case.generate_code("Create add function", test_cases)
        >>> isinstance(code_file, CodeFile)
        True
    """

    def __init__(
        self,
        llm_service: ITestAgentLLMService,
        llm_client: LLMClient,
    ) -> None:
        """Initialize use case.

        Args:
            llm_service: Test agent LLM service for prompt generation.
            llm_client: LLM client for generating code.
        """
        self.llm_service = llm_service
        self.llm_client = llm_client
        self.logger = get_logger("test_agent.generate_code")
        self.debug_enabled = os.getenv("TEST_AGENT_DEBUG_LLM", "").lower() in (
            "1",
            "true",
            "yes",
        )

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
            ValueError: If generated code violates Clean Architecture boundaries.
            Exception: If LLM generation fails.
        """
        tests_str = "\n".join(tc.code for tc in test_cases)
        prompt = self.llm_service.generate_code_prompt(
            requirements, tests_str, source_code
        )

        try:
            self.logger.debug("Calling LLM for code generation")
            response = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2048,
            )
            self.logger.debug(
                "LLM response received",
                extra={
                    "response_length": len(response),
                    "response_lines": len(response.split("\n")),
                },
            )
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}", exc_info=True)
            raise Exception(f"LLM generation failed: {e}") from e

        # Clean and validate generated code
        cleaned_code = self._clean_generated_code(response)

        # Validate syntax
        try:
            ast.parse(cleaned_code)
            self.logger.debug("Generated code syntax validated")
        except SyntaxError as e:
            self.logger.error(
                f"Generated code has syntax errors: {e.msg} at line {e.lineno}",
                extra={"code_preview": cleaned_code[:500]},
            )
            raise ValueError(
                f"Generated code has syntax errors: {e.msg} at line {e.lineno}"
            ) from e

        self._validate_clean_architecture(cleaned_code)

        import uuid

        unique_id = uuid.uuid4().hex[:8]
        code_file = CodeFile(
            path=f"generated_code_{unique_id}.py",
            content=cleaned_code,
            metadata={"source": "llm_generation", "requirements": requirements},
        )

        self.logger.info(
            "Code generation completed",
            extra={
                "file_path": code_file.path,
                "code_length": len(cleaned_code),
                "code_lines": len(cleaned_code.split("\n")),
            },
        )

        return code_file

    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code by removing markdown and explanatory text.

        Args:
            code: Raw generated code from LLM.

        Returns:
            Cleaned code with only Python code.
        """
        # Remove markdown code blocks
        code = re.sub(r"```python\s*\n", "", code)
        code = re.sub(r"```\s*\n", "", code)
        code = re.sub(r"```", "", code)

        # Remove explanatory text at the beginning
        lines = code.split("\n")
        cleaned_lines = []
        in_code = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines at the start
            if not in_code and not stripped:
                continue

            # Start of code (import, def, class, or assignment)
            if stripped.startswith(("import ", "from ", "def ", "class ", "@")) or (
                stripped and "=" in stripped and "(" in stripped
            ):
                in_code = True
                cleaned_lines.append(line)
                continue

            # If we're in code, keep the line
            if in_code:
                cleaned_lines.append(line)
                continue

            # Skip explanatory text (only before code starts)
            if not in_code:
                if any(
                    stripped.startswith(phrase)
                    for phrase in [
                        "Note:",
                        "However:",
                        "But",
                        "Since",
                        "Based on",
                        "The",
                        "This",
                        "These",
                        "We may",
                        "CRITICAL",
                        "Requirements:",
                        "Example:",
                        "Generate",
                        "Follow",
                        "Use",
                        "Write",
                    ]
                ):
                    # Skip explanatory text if it's long or looks like explanation
                    if len(stripped) > 30 or ":" in stripped:
                        continue
                    # Also skip if it's a short sentence without code-like syntax
                    if not any(
                        char in stripped for char in ["=", "(", "[", "{", "@", "#"]
                    ):
                        continue

        return "\n".join(cleaned_lines).strip()

    def _validate_clean_architecture(self, code: str) -> None:
        """Validate Clean Architecture boundaries.

        Args:
            code: Generated code to validate.

        Raises:
            ValueError: If code violates Clean Architecture boundaries.
        """
        forbidden_imports = [
            r"from\s+src\.presentation",
            r"from\s+src\.infrastructure",
            r"import\s+src\.presentation",
            r"import\s+src\.infrastructure",
        ]

        for pattern in forbidden_imports:
            if re.search(pattern, code):
                raise ValueError(
                    f"Clean Architecture violation: code imports from outer layer ({pattern})"
                )
