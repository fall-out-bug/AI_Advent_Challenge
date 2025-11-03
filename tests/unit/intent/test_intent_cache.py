"""Unit tests for IntentCache.

Following TDD: Test-Driven Development.
"""

import pytest
import asyncio

from src.domain.intent.intent_classifier import IntentResult, IntentType
from src.infrastructure.cache.intent_cache import IntentCache


class TestIntentCache:
    """Test suite for IntentCache."""

    @pytest.fixture
    def cache(self):
        """Create IntentCache instance with short TTL for testing."""
        return IntentCache(default_ttl_seconds=1)  # 1 second TTL for tests

    @pytest.fixture
    def sample_result(self):
        """Create sample IntentResult for testing."""
        return IntentResult(
            intent=IntentType.DATA_DIGEST,
            confidence=0.9,
            source="llm",
            entities={"channel_name": "xor", "days": 3},
            latency_ms=2500.0,
        )

    @pytest.mark.asyncio
    async def test_get_set_cache(self, cache, sample_result):
        """Test basic cache get/set operations."""
        message = "digest of xor for 3 days"
        
        # Cache miss initially
        result = await cache.get(message)
        assert result is None
        
        # Set cache
        await cache.set(message, sample_result)
        
        # Cache hit
        result = await cache.get(message)
        assert result is not None
        assert result.intent == IntentType.DATA_DIGEST
        assert result.confidence == 0.9
        assert result.source == "cached"  # Source should be "cached"
        assert result.entities == {"channel_name": "xor", "days": 3}

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache, sample_result):
        """Test cache expiration after TTL."""
        message = "digest of xor"
        await cache.set(message, sample_result, ttl_seconds=0.1)  # Very short TTL
        
        # Should be cached immediately
        result = await cache.get(message)
        assert result is not None
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Should be expired
        result = await cache.get(message)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_case_insensitive(self, cache, sample_result):
        """Test cache is case-insensitive."""
        message1 = "Digest of XOR"
        message2 = "digest of xor"
        
        await cache.set(message1, sample_result)
        
        # Should match regardless of case
        result = await cache.get(message2)
        assert result is not None
        assert result.intent == IntentType.DATA_DIGEST

    @pytest.mark.asyncio
    async def test_cache_normalizes_whitespace(self, cache, sample_result):
        """Test cache normalizes whitespace."""
        message1 = "  digest of xor  "
        message2 = "digest of xor"
        
        await cache.set(message1, sample_result)
        
        # Should match with normalized whitespace
        result = await cache.get(message2)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache, sample_result):
        """Test clearing cache."""
        message = "digest of xor"
        await cache.set(message, sample_result)
        
        assert cache.size() > 0
        
        await cache.clear()
        
        assert cache.size() == 0
        result = await cache.get(message)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_thread_safety(self, cache, sample_result):
        """Test cache is thread-safe."""
        message = "test message"
        
        # Concurrent get/set operations
        async def concurrent_ops():
            await cache.set(message, sample_result)
            return await cache.get(message)
        
        # Run multiple concurrent operations
        results = await asyncio.gather(*[concurrent_ops() for _ in range(10)])
        
        # All should succeed without errors
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_cache_custom_ttl(self, cache, sample_result):
        """Test custom TTL per entry."""
        message1 = "message 1"
        message2 = "message 2"
        
        await cache.set(message1, sample_result, ttl_seconds=0.1)
        await cache.set(message2, sample_result, ttl_seconds=2.0)
        
        await asyncio.sleep(0.2)
        
        # First should be expired
        assert await cache.get(message1) is None
        
        # Second should still be cached
        assert await cache.get(message2) is not None

