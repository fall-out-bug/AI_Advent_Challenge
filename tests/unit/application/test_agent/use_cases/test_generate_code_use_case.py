"""Unit tests for GenerateCodeUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.test_agent.use_cases.generate_code_use_case import (
    GenerateCodeUseCase,
)
from src.domain.test_agent.entities.code_file import CodeFile
from src.domain.test_agent.entities.test_case import TestCase

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = MagicMock()
    service.generate_code_prompt = MagicMock(
        return_value="Generate code for these requirements and tests"
    )
    return service


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = AsyncMock()
    client.generate = AsyncMock(
        return_value="""
def calculate_sum(a: int, b: int) -> int:
    return a + b
"""
    )
    return client


@pytest.fixture
def sample_test_cases():
    """Create sample test cases."""
    return [
        TestCase(
            name="test_calculate_sum",
            code="def test_calculate_sum(): assert calculate_sum(1, 2) == 3",
        )
    ]


async def test_generate_code_returns_code_file(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code returns code file."""
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create a function that adds two numbers"

    result = await use_case.generate_code(requirements, sample_test_cases)

    assert isinstance(result, CodeFile)
    assert result.path is not None
    assert len(result.content) > 0


async def test_generate_code_uses_llm_service(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code uses LLM service."""
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create a function"

    await use_case.generate_code(requirements, sample_test_cases)

    mock_llm_service.generate_code_prompt.assert_called_once()
    assert requirements in mock_llm_service.generate_code_prompt.call_args[0][0]


async def test_generate_code_validates_clean_architecture(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code validates Clean Architecture."""
    mock_llm_client.generate = AsyncMock(
        return_value="from src.presentation import Something  # violates boundaries"
    )
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create code"

    with pytest.raises(ValueError, match="Clean Architecture"):
        await use_case.generate_code(requirements, sample_test_cases)


async def test_generate_code_handles_llm_errors(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code handles LLM errors."""
    mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM error"))
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create code"

    with pytest.raises(Exception, match="LLM generation failed"):
        await use_case.generate_code(requirements, sample_test_cases)


async def test_generate_code_respects_layer_boundaries(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code respects layer boundaries."""
    mock_llm_client.generate = AsyncMock(
        return_value="""
def calculate(a: int, b: int) -> int:
    return a + b
"""
    )
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create code"

    result = await use_case.generate_code(requirements, sample_test_cases)

    assert isinstance(result, CodeFile)
    assert "from src.presentation" not in result.content
    assert "from src.infrastructure" not in result.content


async def test_generate_code_cleans_markdown_blocks(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code removes markdown code blocks."""
    mock_llm_client.generate = AsyncMock(
        return_value="""```python
def calculate(a: int, b: int) -> int:
    return a + b
```"""
    )
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create code"

    result = await use_case.generate_code(requirements, sample_test_cases)

    assert "```python" not in result.content
    assert "```" not in result.content
    assert "def calculate" in result.content


async def test_generate_code_removes_explanatory_text(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code removes explanatory text."""
    mock_llm_client.generate = AsyncMock(
        return_value="""Note: This code implements the calculation.
However, we need to be careful.
def calculate(a: int, b: int) -> int:
    return a + b"""
    )
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create code"

    result = await use_case.generate_code(requirements, sample_test_cases)

    assert "Note:" not in result.content
    assert "However," not in result.content
    assert "def calculate" in result.content


async def test_generate_code_validates_syntax(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code validates Python syntax."""
    mock_llm_client.generate = AsyncMock(
        return_value="""def calculate(a: int, b: int) -> int:
    return a + b
invalid syntax here"""
    )
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create code"

    with pytest.raises(ValueError, match="syntax errors"):
        await use_case.generate_code(requirements, sample_test_cases)


async def test_generate_code_handles_incomplete_code(
    mock_llm_service, mock_llm_client, sample_test_cases
):
    """Test generate_code handles incomplete code."""
    mock_llm_client.generate = AsyncMock(
        return_value="""def calculate(a: int, b: int) -> int:
    return a +"""
    )
    use_case = GenerateCodeUseCase(
        llm_service=mock_llm_service, llm_client=mock_llm_client
    )
    requirements = "Create code"

    with pytest.raises(ValueError, match="syntax errors"):
        await use_case.generate_code(requirements, sample_test_cases)
