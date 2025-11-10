"""Unit tests for code generator agent.

Following TDD principles and the Zen of Python:
- Tests should be simple and readable
- One test per behavior
- Clear assertions
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.agents.base_agent import BaseAgent
from src.domain.agents.code_generator import CodeGeneratorAgent, GeneratorPrompts
from src.domain.messaging.message_schema import (
    CodeGenerationRequest,
    CodeGenerationResponse,
)


# Mock implementation for testing
class MockCodeGenerator(BaseAgent):
    """Concrete implementation for testing."""

    def __init__(self, model_client=None):
        """Initialize code generator."""
        super().__init__(
            model_name="test_model",
            agent_type="generator",
            max_tokens=1500,
            temperature=0.3,
            model_client=model_client,
        )

    async def _prepare_prompt(self, request: CodeGenerationRequest) -> str:
        """Prepare generation prompt."""
        return f"Generate code for: {request.task_description}"

    async def _call_model_for_code(self, prompt: str, max_tokens: int) -> dict:
        """Call model for code generation."""
        return await self._call_model(prompt=prompt, max_tokens=max_tokens)

    async def _extract_and_validate(
        self, response: dict, task_description: str
    ) -> tuple[str, str, object]:
        """Extract and validate code."""
        code = "def hello(): pass"
        tests = "def test_hello(): assert hello() is None"

        # Create a simple metadata object
        class MetadataObj:
            def to_dict(self):
                return {"complexity": "low", "lines_of_code": 2}

        metadata = MetadataObj()
        return code, tests, metadata

    async def validate_generated_code(self, code: str) -> list[str]:
        """Validate generated code."""
        issues = []
        if "def" not in code:
            issues.append("No function definitions found")
        return issues

    async def process(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        """Process code generation request."""
        # Prepare prompt
        prompt = await self._prepare_prompt(request)

        # Call model
        response = await self._call_model_for_code(prompt, request.max_tokens)

        # Extract and validate
        code, tests, metadata = await self._extract_and_validate(
            response, request.task_description
        )

        # Validate code
        await self.validate_generated_code(code)

        # Create response
        return CodeGenerationResponse(
            task_description=request.task_description,
            generated_code=code,
            tests=tests,
            metadata=metadata.to_dict(),
            generation_time=datetime.now(),
            tokens_used=response.get("total_tokens", 0),
        )


class MockModelClient:
    """Mock model client for testing."""

    def __init__(self, response_text="Generated code"):
        """Initialize mock client."""
        self.response_text = response_text

    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """Generate mock response."""
        return {
            "response": self.response_text,
            "total_tokens": 100,
        }


@pytest.mark.asyncio
async def test_code_generator_initialization():
    """Test code generator initialization."""
    generator = MockCodeGenerator()

    assert generator.model_name == "test_model"
    assert generator.agent_type == "generator"
    assert generator.max_tokens == 1500
    assert generator.temperature == 0.3


@pytest.mark.asyncio
async def test_code_generator_process_request():
    """Test processing a generation request."""
    mock_client = MockModelClient()
    generator = MockCodeGenerator(model_client=mock_client)

    request = CodeGenerationRequest(
        task_description="Create a hello function",
        language="python",
        max_tokens=1500,
    )

    response = await generator.process(request)

    assert response.task_description == "Create a hello function"
    assert response.generated_code == "def hello(): pass"
    assert response.tests == "def test_hello(): assert hello() is None"
    assert response.tokens_used == 100


@pytest.mark.asyncio
async def test_code_generator_prepare_prompt():
    """Test preparing generation prompt."""
    generator = MockCodeGenerator()

    request = CodeGenerationRequest(
        task_description="Test task",
        language="python",
    )

    prompt = await generator._prepare_prompt(request)

    assert "Test task" in prompt


@pytest.mark.asyncio
async def test_code_generator_validate_code():
    """Test code validation."""
    generator = MockCodeGenerator()

    # Test with valid code
    valid_code = "def hello(): pass"
    issues = await generator.validate_generated_code(valid_code)
    assert len(issues) == 0

    # Test with invalid code
    invalid_code = "not valid python code {{"
    issues = await generator.validate_generated_code(invalid_code)
    assert len(issues) > 0


@pytest.mark.asyncio
async def test_real_code_generator_initialization():
    """Test real CodeGeneratorAgent initialization."""
    generator = CodeGeneratorAgent(
        model_name="test_model",
        max_tokens=2000,
        temperature=0.5,
    )

    assert generator.model_name == "test_model"
    assert generator.agent_type == "generator"
    assert generator.max_tokens == 2000
    assert generator.temperature == 0.5


@pytest.mark.asyncio
async def test_real_code_generator_prepare_prompt():
    """Test real CodeGeneratorAgent prompt preparation."""
    generator = CodeGeneratorAgent()

    request = CodeGenerationRequest(
        task_description="Create a calculator",
        language="python",
        requirements=["use classes", "add type hints"],
    )

    prompt = generator._prepare_prompt(request)

    assert "Create a calculator" in prompt
    assert "use classes" in prompt
    assert "add type hints" in prompt
    assert "python" in prompt.lower()


@pytest.mark.asyncio
async def test_generator_prompts_get_code_prompt():
    """Test GeneratorPrompts.get_code_generation_prompt."""
    prompt = GeneratorPrompts.get_code_generation_prompt(
        task_description="Test task",
        language="python",
        requirements=["req1", "req2"],
    )

    assert "Test task" in prompt
    assert "req1" in prompt
    assert "req2" in prompt
    assert "Type hints" in prompt
    assert "Docstrings" in prompt


@pytest.mark.asyncio
async def test_generator_prompts_get_test_prompt():
    """Test GeneratorPrompts.get_test_generation_prompt."""
    function_code = "def add(a, b): return a + b"

    prompt = GeneratorPrompts.get_test_generation_prompt(
        function_code=function_code,
        task_description="Test task",
    )

    assert "add(a, b)" in prompt
    assert "Test task" in prompt
    assert "pytest" in prompt.lower()
    assert "edge case" in prompt.lower()


@pytest.mark.asyncio
async def test_generator_prompts_get_refinement_prompt():
    """Test GeneratorPrompts.get_refinement_prompt."""
    code = "def example(): pass"
    feedback = "Add error handling"

    prompt = GeneratorPrompts.get_refinement_prompt(code, feedback)

    assert "example()" in prompt
    assert "Add error handling" in prompt


@pytest.mark.asyncio
async def test_code_generator_validate_with_syntax_error():
    """Test code validation with syntax error."""
    generator = CodeGeneratorAgent()

    invalid_code = """
def broken_code(
    # Missing closing parenthesis
"""

    issues = generator.validate_generated_code(invalid_code)
    assert len(issues) > 0
    assert any("Syntax error" in issue for issue in issues)


@pytest.mark.asyncio
async def test_code_generator_validate_without_functions():
    """Test code validation without function definitions."""
    generator = CodeGeneratorAgent()

    code_without_functions = "x = 5\ny = 10\nprint(x + y)"

    issues = generator.validate_generated_code(code_without_functions)
    assert len(issues) > 0
    assert any("No function definitions found" in issue for issue in issues)


@pytest.mark.asyncio
async def test_code_generator_prepare_prompt_without_requirements():
    """Test prompt preparation without requirements."""
    generator = CodeGeneratorAgent()

    request = CodeGenerationRequest(
        task_description="Simple task",
        language="python",
    )

    prompt = generator._prepare_prompt(request)

    assert "Simple task" in prompt
    assert "python" in prompt.lower()
    assert "Requirements:" not in prompt


@pytest.mark.asyncio
async def test_code_generator_call_model():
    """Test model calling functionality."""
    generator = CodeGeneratorAgent()

    # Create a mock client
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(
        return_value={
            "response": "Generated code here",
            "total_tokens": 50,
        }
    )

    generator.model_client = mock_client

    prompt = "Test prompt"
    response = await generator._call_model_for_code(prompt, 1000)

    assert response["response"] == "Generated code here"
    assert response["total_tokens"] == 50
    mock_client.generate.assert_called_once()
