"""Unit tests for LLMClassifier.

Following TDD: Test-Driven Development.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.intent.intent_classifier import IntentType
from src.domain.intent.llm_classifier import LLMClassifier


class TestLLMClassifier:
    """Test suite for LLMClassifier."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        client.make_request = AsyncMock()
        return client

    @pytest.fixture
    def classifier(self, mock_llm_client):
        """Create LLMClassifier with mocked client."""
        return LLMClassifier(
            llm_client=mock_llm_client,
            model_name="mistral",
            timeout_seconds=5.0,
            temperature=0.2,
        )

    @pytest.mark.asyncio
    async def test_classify_successful(self, classifier, mock_llm_client):
        """Test successful LLM classification."""
        # Mock LLM response
        mock_llm_client.make_request.return_value = '''{
            "intent": "TASK_CREATE",
            "confidence": 0.9,
            "entities": {"title": "buy milk"}
        }'''
        
        result = await classifier.classify("Create a task to buy milk")
        
        assert result.intent == IntentType.TASK_CREATE
        assert result.confidence == 0.9
        assert result.source == "llm"
        assert result.entities.get("title") == "buy milk"
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_classify_with_json_in_text(self, classifier, mock_llm_client):
        """Test parsing JSON from text response."""
        mock_llm_client.make_request.return_value = '''Here is the classification:
        {
            "intent": "DATA_DIGEST",
            "confidence": 0.85,
            "entities": {"channel_name": "xor"}
        }
        That's the result.'''
        
        result = await classifier.classify("digest of xor")
        
        assert result.intent == IntentType.DATA_DIGEST
        assert result.confidence == 0.85
        assert result.entities.get("channel_name") == "xor"

    @pytest.mark.asyncio
    async def test_classify_timeout(self, classifier, mock_llm_client):
        """Test timeout handling."""
        import asyncio
        mock_llm_client.make_request.side_effect = asyncio.TimeoutError()
        
        result = await classifier.classify("Create task")
        
        # Should fallback to IDLE on timeout
        assert result.intent == IntentType.IDLE
        assert result.confidence == 0.3
        assert result.source == "llm"

    @pytest.mark.asyncio
    async def test_classify_parse_error(self, classifier, mock_llm_client):
        """Test JSON parsing error handling."""
        mock_llm_client.make_request.return_value = "Not valid JSON response"
        
        result = await classifier.classify("Create task")
        
        # Should fallback to IDLE on parse error
        assert result.intent == IntentType.IDLE
        assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_classify_empty_response(self, classifier, mock_llm_client):
        """Test empty response handling."""
        mock_llm_client.make_request.return_value = ""
        
        result = await classifier.classify("Create task")
        
        assert result.intent == IntentType.IDLE
        assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_classify_unknown_intent_type(self, classifier, mock_llm_client):
        """Test unknown intent type handling."""
        mock_llm_client.make_request.return_value = '''{
            "intent": "UNKNOWN_INTENT",
            "confidence": 0.8,
            "entities": {}
        }'''
        
        result = await classifier.classify("random message")
        
        # Should default to IDLE for unknown intent
        assert result.intent == IntentType.IDLE

    @pytest.mark.asyncio
    async def test_classify_empty_message(self, classifier):
        """Test empty message handling."""
        result = await classifier.classify("")
        assert result.intent == IntentType.IDLE
        assert result.confidence == 0.5

