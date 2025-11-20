"""Integration tests for CodeSummarizer with real LLM."""

import os
from pathlib import Path

import pytest

from src.infrastructure.clients.llm_client import HTTPLLMClient
from src.infrastructure.test_agent.services.code_summarizer import CodeSummarizer


@pytest.fixture
def llm_client():
    """Create real LLM client for integration tests."""
    llm_url = os.getenv("LLM_URL", "http://localhost:8000")
    llm_model = os.getenv("LLM_MODEL", "gigachat")
    return HTTPLLMClient(url=llm_url, model=llm_model)


@pytest.fixture
def code_summarizer(llm_client):
    """Create CodeSummarizer with real LLM client."""
    return CodeSummarizer(llm_client=llm_client)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_real_python_module(code_summarizer, llm_client):
    """Test summarization of a real Python module."""
    # Arrange
    test_file = (
        Path(__file__).parent.parent.parent.parent.parent.parent
        / "src"
        / "domain"
        / "test_agent"
        / "entities"
        / "code_chunk.py"
    )

    if not test_file.exists():
        pytest.skip("Test file not found")

    code_content = test_file.read_text()

    # Skip if LLM service not available
    try:
        # Test LLM connectivity
        await llm_client.generate("test", max_tokens=10)
    except Exception:
        pytest.skip("LLM service not available")

    # Act
    summary = await code_summarizer.summarize_chunk(code_content)

    # Assert
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert len(summary) < len(code_content) * 0.5  # Summary should be shorter
    # Summary should mention key concepts
    assert (
        "code" in summary.lower()
        or "chunk" in summary.lower()
        or "entity" in summary.lower()
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summary_preserves_critical_info(code_summarizer, llm_client):
    """Test that summary preserves critical information."""
    # Arrange
    code = """
from typing import List, Dict
from src.domain.models import User

class UserService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_user(self, user_id: int) -> User:
        return self.db.find_user(user_id)

    def create_user(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        return self.db.save_user(user)
"""

    # Skip if LLM service not available
    try:
        await llm_client.generate("test", max_tokens=10)
    except Exception:
        pytest.skip("LLM service not available")

    # Act
    summary = await code_summarizer.summarize_chunk(code)

    # Assert
    assert "UserService" in summary or "user" in summary.lower()
    assert (
        "get_user" in summary or "create_user" in summary or "user" in summary.lower()
    )
    # Should preserve type hints or function signatures
    assert "int" in summary or "str" in summary or "User" in summary


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summary_fits_in_token_budget(code_summarizer, llm_client):
    """Test that summary fits within token budget."""
    # Arrange
    from src.infrastructure.test_agent.services.token_counter import TokenCounter

    token_counter = TokenCounter()
    code = (
        """
def complex_function(data: list[dict]) -> dict:
    result = {}
    for item in data:
        if item.get('type') == 'user':
            result[item['id']] = process_user(item)
        elif item.get('type') == 'product':
            result[item['id']] = process_product(item)
        else:
            result[item['id']] = process_default(item)
    return result

def process_user(user_data: dict) -> dict:
    return {'name': user_data['name'], 'role': user_data.get('role', 'user')}

def process_product(product_data: dict) -> dict:
    return {'name': product_data['name'], 'price': product_data['price']}

def process_default(data: dict) -> dict:
    return {'id': data['id'], 'type': data.get('type', 'unknown')}
"""
        * 5
    )  # Make it longer

    # Skip if LLM service not available
    try:
        await llm_client.generate("test", max_tokens=10)
    except Exception:
        pytest.skip("LLM service not available")

    # Act
    summary = await code_summarizer.summarize_chunk(code)

    # Assert
    original_tokens = token_counter.count_tokens(code)
    summary_tokens = token_counter.count_tokens(summary)
    # Summary should be significantly shorter
    assert summary_tokens < original_tokens * 0.5
    # But should still contain key information
    assert "complex_function" in summary or "function" in summary.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_summarize_package_with_multiple_modules(code_summarizer, llm_client):
    """Test summarization of package with multiple modules."""
    # Arrange
    files = [
        "src/domain/test_agent/entities/code_chunk.py",
        "src/domain/test_agent/value_objects/chunking_strategy.py",
        "src/domain/test_agent/interfaces/code_chunker.py",
    ]

    # Verify files exist
    base_path = Path(__file__).parent.parent.parent.parent.parent.parent
    existing_files = []
    for file_path in files:
        full_path = base_path / file_path
        if full_path.exists():
            existing_files.append(file_path)

    if len(existing_files) < 2:
        pytest.skip("Not enough test files found")

    # Skip if LLM service not available
    try:
        await llm_client.generate("test", max_tokens=10)
    except Exception:
        pytest.skip("LLM service not available")

    # Act
    summary = await code_summarizer.summarize_package_structure(existing_files)

    # Assert
    assert isinstance(summary, str)
    assert len(summary) > 0
    # Should mention package structure
    assert (
        "entities" in summary.lower()
        or "value_objects" in summary.lower()
        or "interfaces" in summary.lower()
        or "package" in summary.lower()
        or "module" in summary.lower()
    )
