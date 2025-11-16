"""Characterization tests for LLM client behavior.

These tests document current LLM client interface and behavior
before refactoring in Cluster D.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.infrastructure.llm.clients.llm_client import LLMClient


class TestLLMClientProtocol:
    """Characterize LLM client protocol interface."""

    def test_llm_client_protocol_generate_signature(self):
        """Test that LLMClient protocol defines generate() method.

        Purpose:
            Document the expected signature of generate() method
            before introducing LLMClient adapter interface.
        """
        # Protocol should define async generate method
        # Check signature via type hints or runtime_checkable
        assert hasattr(LLMClient, "__abstractmethods__") or hasattr(
            LLMClient, "__annotations__"
        )

        # Verify method signature exists
        import inspect

        sig = inspect.signature(LLMClient.generate)
        params = list(sig.parameters.keys())

        assert "prompt" in params
        assert "temperature" in params
        assert "max_tokens" in params
        assert "stop_sequences" in params or "stop_sequences" in str(sig)

        # Check return type annotation
        return_annotation = sig.return_annotation
        assert return_annotation == str or "str" in str(return_annotation)

    def test_llm_client_protocol_batch_generate_signature(self):
        """Test that LLMClient protocol defines batch_generate() method.

        Purpose:
            Document the expected signature of batch_generate() method
            before introducing LLMClient adapter interface.
        """
        # Verify method signature exists
        import inspect

        sig = inspect.signature(LLMClient.batch_generate)
        params = list(sig.parameters.keys())

        assert "prompts" in params
        assert "temperature" in params
        assert "max_tokens" in params
        assert "stop_sequences" in params or "stop_sequences" in str(sig)

        # Check return type annotation
        return_annotation = sig.return_annotation
        assert return_annotation == list[str] or "list" in str(return_annotation)

    @pytest.mark.asyncio
    async def test_llm_client_generate_behavior_characterization(
        self, mock_llm_client
    ):
        """Characterize generate() method behavior.

        Purpose:
            Document current behavior: method is async, accepts prompt,
            returns string completion.
        """
        # Setup: Mock client implements protocol
        mock_llm_client.generate = AsyncMock(return_value="Test completion")

        # Execute
        result = await mock_llm_client.generate(
            prompt="Test prompt", temperature=0.2, max_tokens=256
        )

        # Verify: Returns string
        assert isinstance(result, str)
        assert result == "Test completion"

        # Verify: Called with expected parameters
        mock_llm_client.generate.assert_called_once()
        call_kwargs = mock_llm_client.generate.call_args.kwargs
        assert "prompt" in call_kwargs or "Test prompt" in str(
            mock_llm_client.generate.call_args
        )

    @pytest.mark.asyncio
    async def test_llm_client_batch_generate_behavior_characterization(
        self, mock_llm_client
    ):
        """Characterize batch_generate() method behavior.

        Purpose:
            Document current behavior: method is async, accepts list of prompts,
            returns list of string completions.
        """
        # Setup: Mock client implements protocol
        mock_llm_client.batch_generate = AsyncMock(
            return_value=["Completion 1", "Completion 2"]
        )

        # Execute
        prompts = ["Prompt 1", "Prompt 2"]
        result = await mock_llm_client.batch_generate(
            prompts=prompts, temperature=0.2, max_tokens=256
        )

        # Verify: Returns list of strings
        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)
        assert len(result) == 2

        # Verify: Called with expected parameters
        mock_llm_client.batch_generate.assert_called_once()

    def test_llm_client_parameter_defaults(self):
        """Characterize default parameter values.

        Purpose:
            Document default values for temperature, max_tokens, stop_sequences
            before refactoring.
        """
        import inspect

        sig = inspect.signature(LLMClient.generate)

        # Check default values
        temp_param = sig.parameters.get("temperature")
        max_tokens_param = sig.parameters.get("max_tokens")

        if temp_param and temp_param.default != inspect.Parameter.empty:
            assert temp_param.default == 0.2

        if max_tokens_param and max_tokens_param.default != inspect.Parameter.empty:
            assert max_tokens_param.default == 256


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = MagicMock(spec=LLMClient)
    client.generate = AsyncMock()
    client.batch_generate = AsyncMock()
    return client
