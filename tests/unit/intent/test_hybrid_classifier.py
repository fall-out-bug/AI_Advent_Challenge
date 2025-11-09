"""Unit tests for HybridIntentClassifier.

Following TDD: Test-Driven Development.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.intent.hybrid_classifier import HybridIntentClassifier
from src.domain.intent.intent_classifier import IntentResult, IntentType
from src.domain.intent.llm_classifier import LLMClassifier
from src.domain.intent.rule_based_classifier import RuleBasedClassifier
from src.infrastructure.cache.intent_cache import IntentCache


class TestHybridIntentClassifier:
    """Test suite for HybridIntentClassifier."""

    @pytest.fixture
    def rule_classifier(self):
        """Create RuleBasedClassifier instance."""
        return RuleBasedClassifier()

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        client.make_request = AsyncMock()
        return client

    @pytest.fixture
    def llm_classifier(self, mock_llm_client):
        """Create LLMClassifier with mocked client."""
        return LLMClassifier(
            llm_client=mock_llm_client,
            model_name="mistral",
            timeout_seconds=5.0,
        )

    @pytest.fixture
    def cache(self):
        """Create IntentCache instance."""
        return IntentCache(default_ttl_seconds=300)

    @pytest.fixture
    def hybrid_classifier(self, rule_classifier, llm_classifier, cache):
        """Create HybridIntentClassifier instance."""
        return HybridIntentClassifier(
            rule_classifier=rule_classifier,
            llm_classifier=llm_classifier,
            cache=cache,
            confidence_threshold=0.7,
        )

    @pytest.mark.asyncio
    async def test_classify_high_confidence_rule(self, hybrid_classifier):
        """Test high confidence rule-based result is returned directly."""
        result = await hybrid_classifier.classify("Дай мои подписки")

        assert result.intent == IntentType.DATA_SUBSCRIPTION_LIST
        assert result.confidence >= 0.7
        assert result.source == "rule"
        assert result.latency_ms < 100  # Should be fast

    @pytest.mark.asyncio
    async def test_classify_low_confidence_fallback_to_cache(
        self, hybrid_classifier, cache, mock_llm_client
    ):
        """Test fallback to cache when rule confidence is low."""
        message = "ambiguous message that matches rule with low confidence"

        # Pre-populate cache with LLM result
        cached_result = IntentResult(
            intent=IntentType.TASK_CREATE,
            confidence=0.8,
            source="llm",
            entities={},
            latency_ms=2000.0,
        )
        await cache.set(message, cached_result)

        # Create rule result with low confidence
        # (We'll use a message that doesn't match rules well)
        result = await hybrid_classifier.classify(message)

        # Should get cached result
        assert result.source == "cached"
        assert result.intent == IntentType.TASK_CREATE

    @pytest.mark.asyncio
    async def test_classify_low_confidence_fallback_to_llm(
        self, hybrid_classifier, mock_llm_client
    ):
        """Test fallback to LLM when rule confidence is low and cache miss."""
        message = "some ambiguous request that needs LLM"

        # Mock LLM response
        mock_llm_client.make_request.return_value = """{
            "intent": "GENERAL_CHAT",
            "confidence": 0.8,
            "entities": {}
        }"""

        result = await hybrid_classifier.classify(message)

        # Should use LLM result
        assert result.intent == IntentType.GENERAL_CHAT
        assert result.source == "llm"
        assert result.confidence == 0.8

        # Should be cached for next time
        cached = await hybrid_classifier.cache.get(message)
        assert cached is not None
        assert cached.intent == IntentType.GENERAL_CHAT

    @pytest.mark.asyncio
    async def test_classify_llm_failure_fallback_to_rule(
        self, hybrid_classifier, mock_llm_client
    ):
        """Test fallback to rule result when LLM fails."""
        message = "Дай дайджест"

        # Rule should match with high confidence
        rule_result = hybrid_classifier.rule_classifier.classify(message)
        assert rule_result.confidence >= 0.7

        # But mock LLM failure
        mock_llm_client.make_request.side_effect = Exception("LLM error")

        # Hybrid should still work (fallback to rule)
        result = await hybrid_classifier.classify(message)
        assert result.intent in [IntentType.DATA_DIGEST, IntentType.DATA]
        assert result.source == "rule"

    @pytest.mark.asyncio
    async def test_classify_empty_message(self, hybrid_classifier):
        """Test empty message handling."""
        result = await hybrid_classifier.classify("")
        assert result.intent == IntentType.IDLE
        assert result.confidence == 0.5

    @pytest.mark.asyncio
    async def test_classify_caches_meaningful_results(
        self, hybrid_classifier, mock_llm_client
    ):
        """Test that meaningful LLM results are cached."""
        message = "ambiguous message"

        mock_llm_client.make_request.return_value = """{
            "intent": "TASK_CREATE",
            "confidence": 0.85,
            "entities": {"title": "test"}
        }"""

        result1 = await hybrid_classifier.classify(message)
        assert result1.source == "llm"

        # Second call should use cache
        result2 = await hybrid_classifier.classify(message)
        assert result2.source == "cached"
        assert result2.intent == IntentType.TASK_CREATE

    @pytest.mark.asyncio
    async def test_classify_does_not_cache_idle_low_confidence(
        self, hybrid_classifier, mock_llm_client
    ):
        """Test that IDLE results with low confidence are not cached."""
        message = "random text"

        mock_llm_client.make_request.return_value = """{
            "intent": "IDLE",
            "confidence": 0.3,
            "entities": {}
        }"""

        result = await hybrid_classifier.classify(message)

        # Should not be cached (low confidence IDLE)
        cached = await hybrid_classifier.cache.get(message)
        assert cached is None
