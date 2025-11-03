"""Unit tests for mode classifier.

Following TDD principles and testing best practices.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from src.domain.agents.services.mode_classifier import DialogMode, ModeClassifier
from src.domain.interfaces.llm_client import LLMClientProtocol


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response: str = "TASK"):
        self.response = response
        self.close_called = False

    async def make_request(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = None,
        temperature: float = None,
    ) -> str:
        """Mock make_request."""
        return self.response

    async def check_availability(self, model_name: str) -> bool:
        """Mock check_availability."""
        return True

    async def close(self) -> None:
        """Mock close."""
        self.close_called = True


class TestDialogMode:
    """Test DialogMode enum."""

    def test_task_mode_exists(self):
        """Test TASK mode exists."""
        assert DialogMode.TASK == DialogMode("task")

    def test_data_mode_exists(self):
        """Test DATA mode exists."""
        assert DialogMode.DATA == DialogMode("data")

    def test_reminders_mode_exists(self):
        """Test REMINDERS mode exists."""
        assert DialogMode.REMINDERS == DialogMode("reminders")

    def test_idle_mode_exists(self):
        """Test IDLE mode exists."""
        assert DialogMode.IDLE == DialogMode("idle")


class TestModeClassifier:
    """Test ModeClassifier service."""

    @pytest.mark.asyncio
    async def test_classify_task_mode(self):
        """Test classifying TASK mode."""
        mock_llm = MockLLMClient(response="TASK")
        classifier = ModeClassifier(mock_llm)
        mode = await classifier.classify("Create a task to buy milk")
        assert mode == DialogMode.TASK

    @pytest.mark.asyncio
    async def test_classify_data_mode(self):
        """Test classifying DATA mode."""
        mock_llm = MockLLMClient(response="DATA")
        classifier = ModeClassifier(mock_llm)
        mode = await classifier.classify("Show me channel digests")
        assert mode == DialogMode.DATA

    @pytest.mark.asyncio
    async def test_classify_reminders_mode(self):
        """Test classifying REMINDERS mode."""
        mock_llm = MockLLMClient(response="REMINDERS")
        classifier = ModeClassifier(mock_llm)
        mode = await classifier.classify("What are my reminders?")
        assert mode == DialogMode.REMINDERS

    @pytest.mark.asyncio
    async def test_classify_idle_mode(self):
        """Test classifying IDLE mode."""
        mock_llm = MockLLMClient(response="IDLE")
        classifier = ModeClassifier(mock_llm)
        mode = await classifier.classify("Hello, how are you?")
        assert mode == DialogMode.IDLE

    @pytest.mark.asyncio
    async def test_classify_fallback_on_llm_error(self):
        """Test fallback to IDLE when LLM fails."""
        mock_llm = MockLLMClient()
        mock_llm.make_request = AsyncMock(side_effect=Exception("LLM error"))
        classifier = ModeClassifier(mock_llm)
        mode = await classifier.classify("Any message")
        assert mode == DialogMode.IDLE

    @pytest.mark.asyncio
    async def test_parse_response_case_insensitive(self):
        """Test parsing is case insensitive."""
        mock_llm = MockLLMClient(response="task")
        classifier = ModeClassifier(mock_llm)
        mode = await classifier.classify("Create task")
        assert mode == DialogMode.TASK

    @pytest.mark.asyncio
    async def test_parse_response_with_prefix(self):
        """Test parsing mode name even with prefix."""
        mock_llm = MockLLMClient(response="Mode: TASK")
        classifier = ModeClassifier(mock_llm)
        mode = await classifier.classify("Create task")
        assert mode == DialogMode.TASK

    @pytest.mark.asyncio
    async def test_parse_unrecognized_response_falls_back_to_idle(self):
        """Test parsing unrecognized response falls back to IDLE."""
        mock_llm = MockLLMClient(response="UNKNOWN")
        classifier = ModeClassifier(mock_llm)
        mode = await classifier.classify("Any message")
        assert mode == DialogMode.IDLE

    @pytest.mark.asyncio
    async def test_uses_custom_model(self):
        """Test classifier uses custom model."""
        mock_llm = MockLLMClient(response="TASK")
        classifier = ModeClassifier(mock_llm, default_model="custom-model")
        await classifier.classify("Create task")
        # Verify make_request was called
        assert mock_llm.call_count == 1

