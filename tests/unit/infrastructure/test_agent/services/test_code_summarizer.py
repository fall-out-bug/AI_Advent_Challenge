"""Unit tests for CodeSummarizer service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.test_agent.interfaces.code_summarizer import ICodeSummarizer
from src.infrastructure.llm.clients.llm_client import LLMClient


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create mock LLM client."""
    mock = MagicMock(spec=LLMClient)
    mock.generate = AsyncMock()
    return mock


@pytest.fixture
def code_summarizer(mock_llm_client: MagicMock) -> ICodeSummarizer:
    """Create CodeSummarizer instance.

    Note: This will fail until CodeSummarizer is implemented.
    """
    from src.infrastructure.test_agent.services.code_summarizer import CodeSummarizer

    return CodeSummarizer(llm_client=mock_llm_client)


@pytest.mark.asyncio
async def test_summarize_chunk_returns_concise_summary(
    code_summarizer: ICodeSummarizer, mock_llm_client: MagicMock
) -> None:
    """Test summarize_chunk returns concise summary."""
    # Arrange
    code = """
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

def subtract(a: int, b: int) -> int:
    '''Subtract b from a.'''
    return a - b
"""
    expected_summary = "Functions: add(a, b), subtract(a, b)"
    mock_llm_client.generate.return_value = expected_summary

    # Act
    result = await code_summarizer.summarize_chunk(code)

    # Assert
    assert isinstance(result, str)
    assert len(result) < len(code) * 0.3  # Summary < 30% of original
    assert "add" in result.lower() or "subtract" in result.lower()
    mock_llm_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_chunk_preserves_function_signatures(
    code_summarizer: ICodeSummarizer, mock_llm_client: MagicMock
) -> None:
    """Test summarize_chunk preserves function signatures."""
    # Arrange
    code = """
def calculate_total(items: list[dict], tax_rate: float) -> float:
    total = sum(item['price'] for item in items)
    return total * (1 + tax_rate)
"""
    expected_summary = (
        "Function: calculate_total(items: list[dict], tax_rate: float) -> float"
    )
    mock_llm_client.generate.return_value = expected_summary

    # Act
    result = await code_summarizer.summarize_chunk(code)

    # Assert
    assert "calculate_total" in result
    assert "items" in result or "tax_rate" in result
    assert "float" in result or "list" in result


@pytest.mark.asyncio
async def test_summarize_chunk_preserves_dependencies(
    code_summarizer: ICodeSummarizer, mock_llm_client: MagicMock
) -> None:
    """Test summarize_chunk preserves dependencies."""
    # Arrange
    code = """
from typing import List, Dict
from src.domain.models import User

def process_users(users: List[User]) -> Dict[str, int]:
    return {"count": len(users)}
"""
    expected_summary = "Imports: typing.List, typing.Dict, src.domain.models.User. Function: process_users(users: List[User]) -> Dict[str, int]"
    mock_llm_client.generate.return_value = expected_summary

    # Act
    result = await code_summarizer.summarize_chunk(code)

    # Assert
    assert "User" in result or "typing" in result or "List" in result
    assert "process_users" in result


@pytest.mark.asyncio
async def test_summarize_chunk_removes_implementation_details(
    code_summarizer: ICodeSummarizer, mock_llm_client: MagicMock
) -> None:
    """Test summarize_chunk removes implementation details."""
    # Arrange
    code = """
def complex_algorithm(data: list) -> int:
    result = 0
    for i in range(len(data)):
        if i % 2 == 0:
            result += data[i] * 2
        else:
            result += data[i]
    return result
"""
    expected_summary = "Function: complex_algorithm(data: list) -> int"
    mock_llm_client.generate.return_value = expected_summary

    # Act
    result = await code_summarizer.summarize_chunk(code)

    # Assert
    assert "complex_algorithm" in result
    assert "for i in range" not in result
    assert "if i % 2" not in result


@pytest.mark.asyncio
async def test_summarize_package_structure_returns_overview(
    code_summarizer: ICodeSummarizer, mock_llm_client: MagicMock
) -> None:
    """Test summarize_package_structure returns overview."""
    # Arrange
    files = [
        "src/domain/models/user.py",
        "src/domain/models/product.py",
        "src/domain/services/user_service.py",
    ]
    expected_summary = (
        "Package structure: models (User, Product), services (UserService)"
    )
    mock_llm_client.generate.return_value = expected_summary

    # Act
    result = await code_summarizer.summarize_package_structure(files)

    # Assert
    assert isinstance(result, str)
    assert len(result) > 0
    mock_llm_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_package_lists_modules_and_classes(
    code_summarizer: ICodeSummarizer, mock_llm_client: MagicMock
) -> None:
    """Test summarize_package lists modules and classes."""
    # Arrange
    files = [
        "src/domain/test_agent/entities/code_chunk.py",
        "src/domain/test_agent/value_objects/chunking_strategy.py",
    ]
    expected_summary = "Modules: entities (CodeChunk), value_objects (ChunkingStrategy)"
    mock_llm_client.generate.return_value = expected_summary

    # Act
    result = await code_summarizer.summarize_package_structure(files)

    # Assert
    assert "entities" in result.lower() or "value_objects" in result.lower()
    assert "code_chunk" in result.lower() or "chunking" in result.lower()
