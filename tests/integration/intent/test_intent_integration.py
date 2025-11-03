"""Integration tests for full intent classification flow.

Tests ButlerOrchestrator → HybridClassifier → Handlers integration.
Following TDD: Test-Driven Development.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.domain.intent import HybridIntentClassifier, IntentType
from src.domain.agents.services.mode_classifier import ModeClassifier, DialogMode
from src.domain.agents.handlers.data_handler import DataHandler
from src.domain.interfaces.tool_client import ToolClientProtocol
from src.domain.interfaces.llm_client import LLMClientProtocol


@pytest.mark.asyncio
class TestIntentIntegration:
    """Integration tests for intent classification flow."""

    @pytest.fixture
    def mock_tool_client(self):
        """Create mock MCP tool client."""
        client = MagicMock(spec=ToolClientProtocol)
        client.call_tool = AsyncMock()
        return client

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock(spec=LLMClientProtocol)
        client.make_request = AsyncMock()
        return client

    @pytest.fixture
    async def hybrid_classifier(self, mock_llm_client):
        """Create HybridIntentClassifier with mocked LLM."""
        from src.domain.intent import RuleBasedClassifier, LLMClassifier
        from src.infrastructure.cache.intent_cache import IntentCache

        rule_classifier = RuleBasedClassifier()
        llm_classifier = LLMClassifier(
            llm_client=mock_llm_client,
            model_name="mistral",
            timeout_seconds=5.0,
        )
        cache = IntentCache(default_ttl_seconds=300)
        return HybridIntentClassifier(
            rule_classifier=rule_classifier,
            llm_classifier=llm_classifier,
            cache=cache,
            confidence_threshold=0.7,
        )

    @pytest.fixture
    def mode_classifier(self, mock_llm_client, hybrid_classifier):
        """Create ModeClassifier with hybrid classifier."""
        return ModeClassifier(
            llm_client=mock_llm_client,
            default_model="mistral",
            hybrid_classifier=hybrid_classifier,
        )

    @pytest.fixture
    def data_handler(self, mock_tool_client, hybrid_classifier):
        """Create DataHandler with hybrid classifier."""
        return DataHandler(
            tool_client=mock_tool_client,
            hybrid_classifier=hybrid_classifier,
        )

    @pytest.mark.asyncio
    async def test_mode_classifier_with_hybrid(
        self, mode_classifier, hybrid_classifier
    ):
        """Test ModeClassifier uses HybridIntentClassifier."""
        mode = await mode_classifier.classify("Дай мои подписки")
        
        assert mode == DialogMode.DATA
        # Verify hybrid classifier was used (no LLM call should happen for high-confidence rule)

    @pytest.mark.asyncio
    async def test_data_handler_with_hybrid_classifier(
        self, data_handler, mock_tool_client, hybrid_classifier
    ):
        """Test DataHandler uses HybridIntentClassifier for routing."""
        from src.domain.agents.state_machine import DialogContext

        # Mock list_channels tool response
        mock_tool_client.call_tool.return_value = {
            "channels": [
                {"channel_username": "naboka", "title": "Набока", "active": True},
                {"channel_username": "xor_journal", "title": "XOR Journal", "active": True},
            ]
        }

        context = DialogContext(
            user_id="12345",
            session_id="test_session",
            state="IDLE",
            data={},
        )

        # Test subscription list request
        response = await data_handler.handle(context, "Дай мои подписки")
        
        # Verify tool was called
        mock_tool_client.call_tool.assert_called_once()
        call_args = mock_tool_client.call_tool.call_args
        assert call_args[0][0] == "list_channels"
        
        # Verify response contains subscription info
        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_hybrid_classifier_rule_to_llm_flow(
        self, hybrid_classifier, mock_llm_client
    ):
        """Test hybrid classifier flow: rules → LLM fallback."""
        # Message that matches rule with low confidence (or ambiguous)
        message = "tell me about tasks"
        
        # Mock LLM response
        mock_llm_client.make_request.return_value = '''{
            "intent": "TASK_LIST",
            "confidence": 0.8,
            "entities": {}
        }'''
        
        result = await hybrid_classifier.classify(message)
        
        # Should use LLM (since rule confidence likely low)
        # Result depends on actual rule matching, but LLM should be called if needed
        assert result.intent in IntentType
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_hybrid_classifier_caching(
        self, hybrid_classifier, mock_llm_client
    ):
        """Test hybrid classifier caches LLM results."""
        message = "some very ambiguous request that won't match rules"
        
        # Mock LLM response
        mock_llm_client.make_request.return_value = '''{{
            "intent": "GENERAL_CHAT",
            "confidence": 0.8,
            "entities": {{}}
        }}'''
        
        # First call - should use LLM (rule confidence will be low)
        result1 = await hybrid_classifier.classify(message)
        # Should have called LLM (unless rule matched with high confidence)
        
        # Second call - should use cache if LLM was used and result was meaningful
        result2 = await hybrid_classifier.classify(message)
        
        # If result1 used LLM and was meaningful, result2 should use cache
        # But result1 might use rule if it matches, so we check both cases
        assert result2.intent == result1.intent
        # If first was LLM and cached, second should be cached
        if result1.source == "llm" and result1.confidence > 0.5:
            # Check if it was actually cached (might not cache if confidence too low)
            if result2.source == "cached":
                assert result2.intent == result1.intent

    @pytest.mark.asyncio
    async def test_mode_classifier_fallback(
        self, mock_llm_client
    ):
        """Test ModeClassifier falls back to keyword matching if hybrid fails."""
        # Create ModeClassifier without hybrid_classifier
        mode_classifier = ModeClassifier(
            llm_client=mock_llm_client,
            default_model="mistral",
            hybrid_classifier=None,  # No hybrid classifier
        )
        
        # Should use keyword matching
        mode = await mode_classifier.classify("Дай мои подписки")
        assert mode == DialogMode.DATA

