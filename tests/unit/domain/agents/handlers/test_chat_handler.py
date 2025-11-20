"""Unit tests for Chat Handler.

Following TDD principles and testing best practices.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.dtos.butler_dialog_dtos import DialogContext, DialogState
from src.presentation.bot.handlers.chat import ChatHandler


class MockLLMClient:
    """Mock LLM client."""

    def __init__(self):
        self.make_request = AsyncMock(return_value="Hello! How can I help?")
        self.check_availability = AsyncMock(return_value=True)
        self.close = AsyncMock()


class TestChatHandler:
    """Test ChatHandler."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        return MockLLMClient()

    @pytest.fixture
    def handler(self, mock_llm_client):
        """Create handler instance."""
        return ChatHandler(llm_client=mock_llm_client, default_model="mistral")

    @pytest.mark.asyncio
    async def test_handle_returns_llm_response(self, handler, mock_llm_client):
        """Test handler returns LLM response."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        response = await handler.handle(context, "Hello")
        assert "Hello" in response or "help" in response.lower()
        mock_llm_client.make_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_uses_correct_prompt(self, handler, mock_llm_client):
        """Test handler uses correct prompt format."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        await handler.handle(context, "Test message")
        call_args = mock_llm_client.make_request.call_args
        prompt = call_args[1]["prompt"]
        assert "Test message" in prompt
        assert "Butler" in prompt

    @pytest.mark.asyncio
    async def test_handle_handles_llm_error(self, handler, mock_llm_client):
        """Test error handling when LLM fails."""
        context = DialogContext(
            state=DialogState.IDLE,
            user_id="123",
            session_id="456",
        )
        mock_llm_client.make_request = AsyncMock(side_effect=Exception("LLM error"))
        response = await handler.handle(context, "Hello")
        response_lower = response.lower()
        assert (
            "помочь" in response_lower
            or "создать задачу" in response_lower
            or "help" in response_lower
        )
