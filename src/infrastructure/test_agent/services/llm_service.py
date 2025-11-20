"""Test agent LLM service for prompt generation."""

import os
from pathlib import Path

from src.domain.test_agent.interfaces.llm_service import ITestAgentLLMService
from src.infrastructure.llm.clients.llm_client import LLMClient
from src.infrastructure.logging import get_logger


class TestAgentLLMService:
    """
    Test agent LLM service implementing ITestAgentLLMService.

    Purpose:
        Generates prompts for test generation and code generation using templates.

    Example:
        >>> from src.infrastructure.llm.clients.llm_client import LLMClient
        >>> service = TestAgentLLMService(llm_client=llm_client)
        >>> prompt = service.generate_tests_prompt("def add(a, b): return a + b")
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize service with LLM client.

        Args:
            llm_client: LLMClient Protocol implementation.
        """
        self.llm_client = llm_client
        self.logger = get_logger("test_agent.llm_service")
        self.debug_enabled = os.getenv("TEST_AGENT_DEBUG_LLM", "").lower() in (
            "1",
            "true",
            "yes",
        )
        self.debug_output_dir = Path(
            os.getenv("TEST_AGENT_DEBUG_DIR", "/tmp/test_agent_debug")
        )

    def generate_tests_prompt(self, code: str) -> str:
        """Generate prompt for test generation.

        Args:
            code: Source code to generate tests for.

        Returns:
            Formatted prompt string for LLM.
        """
        if self.debug_enabled:
            self.logger.debug(
                "Generating test prompt",
                extra={
                    "code_length": len(code),
                    "code_lines": len(code.split("\n")),
                    "code_preview": code[:200] + "..." if len(code) > 200 else code,
                },
            )

        prompt = f"""Generate comprehensive unit tests for the following Python code.
Follow pytest conventions and ensure 100% coverage.

Code to test:
```python
{code}
```

CRITICAL: The source code above will be included in the same file BEFORE your tests.
This means all functions and classes from the source code will be directly available.
You do NOT need to import anything - just call the functions directly by their names.

Example:
If the source code defines: def add(a, b): return a + b
Your test should call: result = add(2, 3)

Requirements:
- Use pytest framework
- IMPORTANT: If using pytest.raises, pytest.fixture, or any pytest functions, you MUST include: import pytest
- Write test functions with names starting with 'test_'
- Test all functions, edge cases, and error conditions
- Include docstrings for test functions
- Ensure all tests are valid Python code
- IMPORTANT: Call functions directly by name (e.g., add(2, 3), not source_file.add(2, 3))
- The source code will be in the same file, so functions are in the global scope

CRITICAL RULES - READ CAREFULLY:
- Generate ONLY test functions (def test_*)
- DO NOT redefine or modify the source code functions
- DO NOT create new versions of the source functions
- DO NOT add function definitions that match source function names
- ONLY write test functions that CALL the existing functions
- NO explanatory text, comments, or notes outside of code
- NO markdown formatting
- NO text explanations before or after the code
- Start directly with 'def test_' functions
- Each test function must be valid Python code
- Do NOT include any text that is not Python code
- Do NOT include function definitions that are not test functions

Example of CORRECT output:
import pytest

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2

def test_divide_error():
    import pytest
    with pytest.raises(ValueError):
        divide(10, 0)

Example of INCORRECT output (DO NOT DO THIS):
def add(a, b):  # WRONG - do not redefine source functions
    return a + b

Generate only test functions starting with 'def test_'. No function redefinitions, no explanations:"""

        if self.debug_enabled:
            self._save_debug_output("prompt", prompt, code)
            self.logger.debug(
                "Test prompt generated",
                extra={
                    "prompt_length": len(prompt),
                    "prompt_preview": (
                        prompt[:300] + "..." if len(prompt) > 300 else prompt
                    ),
                },
            )

        return prompt

    def generate_code_prompt(
        self, requirements: str, tests: str, source_code: str = ""
    ) -> str:
        """Generate prompt for code generation.

        Args:
            requirements: Requirements description.
            tests: Test cases as string.
            source_code: Optional source code for reference (to match structure).

        Returns:
            Formatted prompt string for LLM.
        """
        source_context = ""
        if source_code:
            source_context = f"""
IMPORTANT: Reference source code structure:
```python
{source_code[:500]}  # (truncated for context)
```

CRITICAL: Match the structure of the source code:
- If source code uses functions (def add(...)), generate functions, not classes
- If source code uses classes (class Calculator), generate classes
- Preserve the same API and function/class names as in the source code
- Do not change the structure (functions vs classes) unless explicitly required
"""

        prompt = f"""Generate Python implementation code that satisfies the following requirements and passes all provided tests.
{source_context}
Requirements:
{requirements}

Test cases:
```python
{tests}
```

Requirements:
- Implement all functions and classes needed to pass the tests
- Match the structure of the source code (functions vs classes)
- Follow Clean Architecture principles
- Use type hints (List, Dict, Optional, Union, Tuple, Any, etc. from typing module)
- IMPORTANT: If using type hints from typing (List, Dict, Optional, Any, etc.), include: from typing import List, Dict, Optional, Any, ...
- CRITICAL: Use 'Any' (capitalized) from typing, NOT 'any' (lowercase) - 'any' is a Python built-in function
- Include all necessary imports at the top of the file
- Include docstrings
- Ensure code is production-ready

Generate only the implementation code, no explanations:"""

        if self.debug_enabled:
            self.logger.debug(
                "Code generation prompt created",
                extra={
                    "requirements_length": len(requirements),
                    "tests_length": len(tests),
                },
            )

        return prompt

    def _save_debug_output(
        self, stage: str, content: str, source_code: str = ""
    ) -> None:
        """Save debug output to file.

        Args:
            stage: Stage name (e.g., 'prompt', 'response').
            content: Content to save.
            source_code: Optional source code for context.
        """
        if not self.debug_enabled:
            return

        try:
            self.debug_output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(os.getenv("TEST_AGENT_DEBUG_TIMESTAMP", "0")) or 0

            if stage == "prompt":
                file_path = self.debug_output_dir / f"prompt_{timestamp}.txt"
                with open(file_path, "w") as f:
                    f.write(f"SOURCE CODE:\n{source_code}\n\n")
                    f.write(f"PROMPT:\n{content}\n")
                self.logger.debug(f"Saved prompt to {file_path}")
            elif stage == "response":
                file_path = self.debug_output_dir / f"response_{timestamp}.txt"
                with open(file_path, "w") as f:
                    f.write(f"SOURCE CODE:\n{source_code}\n\n")
                    f.write(f"LLM RESPONSE:\n{content}\n")
                self.logger.debug(f"Saved response to {file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to save debug output: {e}")
