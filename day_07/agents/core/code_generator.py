"""Code generator agent implementation."""

import ast
import logging
from datetime import datetime
from typing import List, Optional

from agents.core.base_agent import BaseAgent
from communication.message_schema import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    TaskMetadata,
)
from constants import GENERATOR_MAX_TOKENS, GENERATOR_TEMPERATURE
from exceptions import CodeGenerationError, ValidationError
from prompts.generator_prompts import GeneratorPrompts

# Configure logging
logger = logging.getLogger(__name__)


class CodeGeneratorAgent(BaseAgent):
    """Agent responsible for generating Python code and tests."""

    def __init__(
        self,
        model_name: str = "starcoder",
        max_tokens: int = GENERATOR_MAX_TOKENS,
        temperature: float = GENERATOR_TEMPERATURE,
        external_provider: Optional[str] = None,
    ):
        """Initialize the code generator agent.

        Args:
            model_name: Name of the model to use (starcoder, mistral, qwen, tinyllama)
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation (lower for more deterministic code)
            external_provider: External API provider name (if using external API)
        """
        super().__init__(
            model_name=model_name,
            agent_type="generator",
            max_tokens=max_tokens,
            temperature=temperature,
            external_provider=external_provider,
        )
        self.prompts = GeneratorPrompts()

    async def process(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        """Process a code generation request.

        Args:
            request: Code generation request

        Returns:
            Code generation response

        Raises:
            Exception: If model request fails
            ValueError: If response parsing fails
        """
        try:
            logger.info(
                f"Processing code generation request: {request.task_description}"
            )

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
                metadata=metadata,
                generation_time=datetime.now(),
                tokens_used=response.get("total_tokens", 0),
            )

        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Code generation failed: {str(e)}")
            raise CodeGenerationError(f"Model request failed: {str(e)}") from e
        except ValueError as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Response parsing failed: {str(e)}")
            raise ValidationError(f"Invalid response format: {str(e)}") from e

    def _prepare_prompt(self, request: CodeGenerationRequest) -> str:
        """Prepare the generation prompt.

        Args:
            request: Code generation request

        Returns:
            Formatted prompt string
        """
        return self.prompts.get_code_generation_prompt(
            task_description=request.task_description,
            language=request.language,
            requirements=request.requirements,
        )

    async def _call_model_for_code(self, prompt: str, max_tokens: int) -> dict:
        """Call the model for code generation.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens for generation

        Returns:
            Model response

        Raises:
            Exception: If model call fails
        """
        return await self._call_model(prompt=prompt, max_tokens=max_tokens)

    async def _extract_and_validate(
        self, response: dict, task_description: str
    ) -> tuple[str, str, TaskMetadata]:
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
        metadata = self._extract_metadata_from_response(response_text)

        # If tests are empty, try to generate them separately
        if not tests.strip():
            logger.info("No tests found in response, generating separately...")
            tests = await self._generate_tests_separately(
                generated_code, task_description
            )

        # Validate extracted code
        validation_issues = self.validate_generated_code(generated_code)
        if validation_issues:
            logger.warning(f"Code validation issues: {validation_issues}")

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
            test_prompt = self.prompts.get_test_generation_prompt(
                function_code=function_code, task_description=task_description
            )

            response = await self._call_model(prompt=test_prompt, max_tokens=800)

            response_text = response.get("response", "")
            return self._extract_tests_from_response(response_text)

        except Exception:
            # Return a basic test template if generation fails
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
    # Test basic functionality
    # result = {func_name}(test_input)
    # assert result == expected_output
    # 
    # Example for a function that returns a value:
    # assert {func_name}(1) == expected_result
    # 
    # Example for a function that modifies data:
    # data = [1, 2, 3]
    # {func_name}(data)
    # assert data == expected_state
    pass

def test_{func_name}_edge_cases():
    """Test {func_name} with edge cases and boundary conditions."""
    # Test edge cases like empty inputs, None values, extreme values
    # 
    # Example edge cases:
    # - Empty lists/strings: {func_name}([])
    # - None values: {func_name}(None)
    # - Zero values: {func_name}(0)
    # - Large values: {func_name}(999999)
    pass

def test_{func_name}_error_conditions():
    """Test {func_name} error handling and invalid inputs."""
    # Test error conditions and exception handling
    # 
    # Example error tests:
    # with pytest.raises(ValueError):
    #     {func_name}(invalid_input)
    # 
    # with pytest.raises(TypeError):
    #     {func_name}(wrong_type_input)
    pass'''

    async def refine_code(self, code: str, feedback: str) -> str:
        """Refine code based on feedback.

        Args:
            code: Original code
            feedback: Feedback to incorporate

        Returns:
            Refined code
        """
        try:
            prompt = self.prompts.get_refinement_prompt(code=code, feedback=feedback)

            response = await self._call_model(prompt=prompt, max_tokens=1000)

            response_text = response.get("response", "")
            return self._extract_code_from_response(response_text)

        except Exception:
            # Return original code if refinement fails
            return code

    def validate_generated_code(self, code: str) -> List[str]:
        """Validate generated code for basic issues.

        Args:
            code: Generated code to validate

        Returns:
            List of validation issues
        """
        issues = []

        # Check for basic syntax issues using ast.parse (safer than compile)
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {str(e)}")

        # Check for imports
        if "import" not in code and "from" not in code:
            issues.append("No imports found - code might be incomplete")

        # Check for function definitions
        if "def " not in code:
            issues.append("No function definitions found")

        # Check for docstrings
        if '"""' not in code and "'''" not in code:
            issues.append("No docstrings found")

        # Check for type hints
        if ": " not in code and " -> " not in code:
            issues.append("No type hints found")

        return issues
