"""Code generator agent implementation.

Following Clean Architecture and the Zen of Python:
- Beautiful is better than ugly
- Simple is better than complex
- Readability counts
"""

import ast
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from src.domain.agents.base_agent import BaseAgent, TaskMetadata
from src.domain.messaging.message_schema import (
    CodeGenerationRequest,
    CodeGenerationResponse,
)

# Configure logging
logger = logging.getLogger(__name__)


class CodeGeneratorAgent(BaseAgent):
    """Agent responsible for generating Python code and tests."""

    def __init__(
        self,
        model_name: str = "starcoder",
        max_tokens: int = 1500,
        temperature: float = 0.3,
        model_client: Optional[object] = None,
    ):
        """Initialize the code generator agent.

        Args:
            model_name: Name of the model to use
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation
            model_client: Model client for making requests
        """
        super().__init__(
            model_name=model_name,
            agent_type="generator",
            max_tokens=max_tokens,
            temperature=temperature,
            model_client=model_client,
        )

    async def process(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        """Process a code generation request.

        Args:
            request: Code generation request

        Returns:
            Code generation response

        Raises:
            Exception: If model request fails
        """
        try:
            logger.info(f"Processing code generation: {request.task_description}")

            # Prepare prompt and call model
            prompt = self._prepare_prompt(request)
            response = await self._call_model_for_code(prompt, request.max_tokens)

            # Extract and validate results
            generated_code, tests, metadata = await self._extract_and_validate(
                response, request.task_description
            )

            return CodeGenerationResponse(
                task_description=request.task_description,
                generated_code=generated_code,
                tests=tests,
                metadata=metadata.to_dict() if hasattr(metadata, 'to_dict') else metadata,
                generation_time=datetime.now(),
                tokens_used=response.get("total_tokens", 0),
            )

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Code generation failed: {str(e)}")
            raise

    def _prepare_prompt(self, request: CodeGenerationRequest) -> str:
        """Prepare the generation prompt.

        Args:
            request: Code generation request

        Returns:
            Formatted prompt string
        """
        prompt = f"Task: {request.task_description}\n"
        prompt += f"Language: {request.language}\n"

        if request.requirements:
            prompt += f"Requirements:\n"
            for req in request.requirements:
                prompt += f"- {req}\n"

        prompt += "\nGenerate the code with tests following Python best practices."

        return prompt

    async def _call_model_for_code(self, prompt: str, max_tokens: int) -> dict:
        """Call the model for code generation.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens for generation

        Returns:
            Model response
        """
        return await self._call_model(prompt=prompt, max_tokens=max_tokens)

    async def _extract_and_validate(
        self, response: dict, task_description: str
    ) -> Tuple[str, str, TaskMetadata]:
        """Extract and validate code, tests, and metadata from response.

        Args:
            response: Model response
            task_description: Original task description

        Returns:
            Tuple of (generated_code, tests, metadata)

        Raises:
            ValueError: If extraction fails
        """
        response_text = response.get("response", "")

        # Extract code and tests
        generated_code = self._extract_code_from_response(response_text)
        tests = self._extract_tests_from_response(response_text)

        # If tests are empty, try to generate them separately
        if not tests.strip():
            logger.info("No tests found, generating separately...")
            tests = await self._generate_tests_separately(
                generated_code, task_description
            )

        # Validate extracted code
        validation_issues = self.validate_generated_code(generated_code)
        if validation_issues:
            logger.warning(f"Code validation issues: {validation_issues}")

        # Extract metadata
        metadata = self._extract_metadata_from_response(response_text)

        return generated_code, tests, metadata

    async def _generate_tests_separately(
        self, function_code: str, task_description: str
    ) -> str:
        """Generate tests separately if not included in main response.

        Args:
            function_code: The function to test
            task_description: Original task description

        Returns:
            Generated test code
        """
        try:
            test_prompt = (
                f"Generate pytest tests for this function:\n\n"
                f"```python\n{function_code}\n```\n\n"
                f"Task: {task_description}\n"
                f"Include comprehensive test cases with edge cases."
            )

            response = await self._call_model(prompt=test_prompt, max_tokens=800)
            response_text = response.get("response", "")
            return self._extract_tests_from_response(response_text)

        except Exception as e:
            logger.warning(f"Test generation failed: {e}")
            return self._create_basic_test_template(function_code)

    def _create_basic_test_template(self, function_code: str) -> str:
        """Create a basic test template when test generation fails.

        Args:
            function_code: The function to test

        Returns:
            Basic test template
        """
        # Extract function name
        import re

        func_match = re.search(r"def\s+(\w+)\s*\(", function_code)
        if not func_match:
            return "# No function found to test"

        func_name = func_match.group(1)

        return f'''import pytest

def test_{func_name}():
    """Test {func_name} function with basic functionality."""
    pass

def test_{func_name}_edge_cases():
    """Test {func_name} with edge cases."""
    pass
'''

    def validate_generated_code(self, code: str) -> List[str]:
        """Validate generated code for basic issues.

        Args:
            code: Generated code to validate

        Returns:
            List of validation issues
        """
        issues = []

        # Check for basic syntax issues using ast.parse
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {str(e)}")

        # Check for function definitions
        if "def " not in code:
            issues.append("No function definitions found")

        return issues


class GeneratorPrompts:
    """Prompts for code generation."""

    @staticmethod
    def get_code_generation_prompt(
        task_description: str,
        language: str = "python",
        requirements: Optional[List[str]] = None,
    ) -> str:
        """Get code generation prompt.

        Args:
            task_description: Description of the task
            language: Programming language
            requirements: Additional requirements

        Returns:
            Formatted prompt
        """
        requirements = requirements or []

        prompt = f"Generate Python code for: {task_description}\n\n"

        if requirements:
            prompt += "Requirements:\n"
            for req in requirements:
                prompt += f"- {req}\n"
            prompt += "\n"

        prompt += "Include:\n"
        prompt += "- Type hints\n"
        prompt += "- Docstrings\n"
        prompt += "- Best practices\n"
        prompt += "- Unit tests with pytest\n"

        return prompt

    @staticmethod
    def get_test_generation_prompt(function_code: str, task_description: str) -> str:
        """Get test generation prompt.

        Args:
            function_code: The function to test
            task_description: Original task description

        Returns:
            Formatted prompt
        """
        return f"""Generate comprehensive pytest tests for this function:
        
```python
{function_code}
```

Task: {task_description}

Include:
- Basic functionality tests
- Edge case tests
- Error handling tests
"""

    @staticmethod
    def get_refinement_prompt(code: str, feedback: str) -> str:
        """Get code refinement prompt.

        Args:
            code: Original code
            feedback: Feedback to incorporate

        Returns:
            Formatted prompt
        """
        return f"""Refine this code based on feedback:

Original code:
```python
{code}
```

Feedback:
{feedback}

Provide improved code with all feedback addressed.
"""
