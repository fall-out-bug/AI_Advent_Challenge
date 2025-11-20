"""Error path tests for ModeClassifier.

Following TDD principles: test error handling and fallback behavior.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.agents.services.mode_classifier import DialogMode, ModeClassifier
from src.domain.interfaces.llm_client import LLMClientProtocol


@pytest.fixture
def mock_llm_client():
    """Create mock LLM client."""
    return MagicMock(spec=LLMClientProtocol)


@pytest.mark.asyncio
async def test_classify_handles_llm_exception(mock_llm_client):
    """Test classify() falls back to IDLE when LLM raises exception.

    Args:
        mock_llm_client: Mock LLM client.
    """
    # Setup: LLM client raises exception
    mock_llm_client.make_request = AsyncMock(side_effect=Exception("LLM error"))

    classifier = ModeClassifier(llm_client=mock_llm_client, default_model="mistral")

    # Execute
    result = await classifier.classify("Test message")

    # Verify: Falls back to IDLE
    assert result == DialogMode.IDLE


@pytest.mark.asyncio
async def test_classify_handles_connection_error(mock_llm_client):
    """Test classify() handles connection errors.

    Args:
        mock_llm_client: Mock LLM client.
    """
    # Setup: Connection error
    mock_llm_client.make_request = AsyncMock(
        side_effect=ConnectionError("Connection failed")
    )

    classifier = ModeClassifier(llm_client=mock_llm_client, default_model="mistral")

    # Execute
    result = await classifier.classify("Test message")

    # Verify: Falls back to IDLE
    assert result == DialogMode.IDLE


@pytest.mark.asyncio
async def test_classify_handles_timeout(mock_llm_client):
    """Test classify() handles timeout errors.

    Args:
        mock_llm_client: Mock LLM client.
    """
    import asyncio

    # Setup: Timeout error
    mock_llm_client.make_request = AsyncMock(
        side_effect=asyncio.TimeoutError("Timeout")
    )

    classifier = ModeClassifier(llm_client=mock_llm_client, default_model="mistral")

    # Execute
    result = await classifier.classify("Test message")

    # Verify: Falls back to IDLE
    assert result == DialogMode.IDLE


@pytest.mark.asyncio
async def test_parse_response_handles_unparseable_response(mock_llm_client):
    """Test _parse_response() handles unparseable responses.

    Args:
        mock_llm_client: Mock LLM client.
    """
    # Setup: LLM returns garbage
    mock_llm_client.make_request = AsyncMock(return_value="Garbage response 12345")

    classifier = ModeClassifier(llm_client=mock_llm_client, default_model="mistral")

    # Execute
    result = await classifier.classify("Test message")

    # Verify: Falls back to IDLE
    assert result == DialogMode.IDLE


@pytest.mark.asyncio
async def test_parse_response_handles_empty_response(mock_llm_client):
    """Test _parse_response() handles empty responses.

    Args:
        mock_llm_client: Mock LLM client.
    """
    # Setup: LLM returns empty string
    mock_llm_client.make_request = AsyncMock(return_value="")

    classifier = ModeClassifier(llm_client=mock_llm_client, default_model="mistral")

    # Execute
    result = await classifier.classify("Test message")

    # Verify: Falls back to IDLE
    assert result == DialogMode.IDLE


@pytest.mark.asyncio
async def test_parse_response_handles_whitespace_only(mock_llm_client):
    """Test _parse_response() handles whitespace-only responses.

    Args:
        mock_llm_client: Mock LLM client.
    """
    # Setup: LLM returns only whitespace
    mock_llm_client.make_request = AsyncMock(return_value="   \n\t  ")

    classifier = ModeClassifier(llm_client=mock_llm_client, default_model="mistral")

    # Execute
    result = await classifier.classify("Test message")

    # Verify: Falls back to IDLE
    assert result == DialogMode.IDLE


@pytest.mark.asyncio
async def test_parse_response_case_insensitive(mock_llm_client):
    """Test _parse_response() is case-insensitive.

    Args:
        mock_llm_client: Mock LLM client.
    """
    # Setup: LLM returns lowercase
    mock_llm_client.make_request = AsyncMock(return_value="task")

    classifier = ModeClassifier(llm_client=mock_llm_client, default_model="mistral")

    # Execute
    result = await classifier.classify("Test message")

    # Verify: Parses correctly
    assert result == DialogMode.TASK


@pytest.mark.asyncio
async def test_parse_response_with_mode_in_text(mock_llm_client):
    """Test _parse_response() finds mode name within text.

    Args:
        mock_llm_client: Mock LLM client.
    """
    # Setup: LLM returns mode embedded in text
    mock_llm_client.make_request = AsyncMock(
        return_value="The mode is DATA for this request"
    )

    classifier = ModeClassifier(llm_client=mock_llm_client, default_model="mistral")

    # Execute
    result = await classifier.classify("Test message")

    # Verify: Parses correctly
    assert result == DialogMode.DATA


@pytest.mark.asyncio
async def test_classify_passes_correct_parameters(mock_llm_client):
    """Test classify() passes correct parameters to LLM.

    Args:
        mock_llm_client: Mock LLM client.
    """
    # Setup
    mock_llm_client.make_request = AsyncMock(return_value="TASK")

    classifier = ModeClassifier(
        llm_client=mock_llm_client, default_model="custom_model"
    )

    # Execute
    await classifier.classify("Create a task")

    # Verify: Correct parameters passed
    mock_llm_client.make_request.assert_called_once()
    call_kwargs = mock_llm_client.make_request.call_args[1]
    assert call_kwargs["model_name"] == "custom_model"
    assert call_kwargs["max_tokens"] == 10
    assert call_kwargs["temperature"] == 0.1
    assert "Create a task" in mock_llm_client.make_request.call_args[1]["prompt"]
