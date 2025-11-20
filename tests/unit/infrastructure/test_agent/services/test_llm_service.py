"""Unit tests for TestAgentLLMService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.test_agent.services.llm_service import TestAgentLLMService


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    client = AsyncMock()
    client.generate = AsyncMock(return_value="Generated response")
    return client


def test_generate_tests_prompt_creates_valid_prompt(mock_llm_client):
    """Test generate_tests_prompt creates valid prompt."""
    service = TestAgentLLMService(llm_client=mock_llm_client)
    code = "def calculate_sum(a, b): return a + b"

    prompt = service.generate_tests_prompt(code)

    assert isinstance(prompt, str)
    assert "calculate_sum" in prompt
    assert "test" in prompt.lower()
    assert len(prompt) > 0


def test_generate_code_prompt_creates_valid_prompt(mock_llm_client):
    """Test generate_code_prompt creates valid prompt."""
    service = TestAgentLLMService(llm_client=mock_llm_client)
    requirements = "Create a function that adds two numbers"
    tests = "def test_add(): assert add(1, 2) == 3"

    prompt = service.generate_code_prompt(requirements, tests)

    assert isinstance(prompt, str)
    assert "add" in prompt
    assert "function" in prompt.lower()
    assert len(prompt) > 0


def test_service_uses_llm_client_protocol(mock_llm_client):
    """Test service uses LLMClient Protocol."""
    service = TestAgentLLMService(llm_client=mock_llm_client)

    assert service.llm_client is not None
    assert hasattr(service.llm_client, "generate")


def test_service_handles_llm_errors(mock_llm_client):
    """Test service handles LLM errors."""
    mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM error"))
    service = TestAgentLLMService(llm_client=mock_llm_client)

    # Service should not crash when generating prompts
    prompt = service.generate_tests_prompt("code")
    assert isinstance(prompt, str)
