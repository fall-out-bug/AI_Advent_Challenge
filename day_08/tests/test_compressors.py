"""
Tests for compression strategies.

Tests BaseCompressor, TruncationCompressor, KeywordsCompressor,
and CompressionStrategyFactory.
"""

import pytest
from unittest.mock import Mock, MagicMock
from core.compressors import (
    BaseCompressor,
    TruncationCompressor,
    KeywordsCompressor,
    CompressionStrategy,
    CompressionStrategyFactory,
)
from core.interfaces.protocols import TokenCounterProtocol
from models.data_models import CompressionResult, TokenInfo


class MockTokenCounter(TokenCounterProtocol):
    """Mock token counter for testing."""
    
    def __init__(self, token_counts: dict = None):
        self.token_counts = token_counts or {}
    
    def count_tokens(self, text: str, model_name: str = "starcoder") -> TokenInfo:
        """Mock token counting."""
        count = self.token_counts.get(text, len(text.split()))
        return TokenInfo(
            count=count,
            estimated_cost=0.0,
            model_name=model_name
        )
    
    def get_model_limits(self, model_name: str, limit_profile: str = "practical"):
        """Mock model limits."""
        return Mock()
    
    def check_limit_exceeded(self, text: str, model_name: str = "starcoder"):
        """Mock limit check."""
        return Mock()
    
    def estimate_compression_target(self, text: str, model_name: str = "starcoder"):
        """Mock compression target."""
        return Mock()


class TestBaseCompressor:
    """Test BaseCompressor abstract class."""
    
    def test_cannot_instantiate_base_class(self):
        """Test that BaseCompressor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseCompressor(MockTokenCounter())


class TestTruncationCompressor:
    """Test TruncationCompressor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.token_counter = MockTokenCounter({
            "short text": 5,
            "This is a very long text that needs compression. It has multiple sentences. Each sentence adds to the token count. We need to compress this effectively.": 25,
            "First sentence. Middle part with many words. Last sentence.": 15,
            "First sentence. Last sentence.": 8,
        })
        self.compressor = TruncationCompressor(self.token_counter)
    
    def test_no_compression_when_under_limit(self):
        """Test no compression when text is under token limit."""
        result = self.compressor.compress("short text", max_tokens=10, model_name="starcoder")
        
        assert result.original_text == "short text"
        assert result.compressed_text == "short text"
        assert result.compression_ratio == 1.0
        assert result.strategy_used == "no_compression"
    
    def test_compression_with_multiple_sentences(self):
        """Test compression with multiple sentences."""
        text = "This is a very long text that needs compression. It has multiple sentences. Each sentence adds to the token count. We need to compress this effectively."
        
        result = self.compressor.compress(text, max_tokens=15, model_name="starcoder")
        
        assert result.original_text == text
        assert result.compressed_text != text
        assert result.compression_ratio < 1.0
        assert result.strategy_used == "truncation"
        assert "..." in result.compressed_text
    
    def test_compression_with_few_sentences(self):
        """Test compression with few sentences (word-based truncation)."""
        text = "First sentence. Last sentence."
        
        result = self.compressor.compress(text, max_tokens=5, model_name="starcoder")
        
        assert result.compressed_text != text
        assert result.strategy_used == "truncation"
    
    def test_strategy_name(self):
        """Test strategy name."""
        assert self.compressor._get_strategy_name() == "truncation"


class TestKeywordsCompressor:
    """Test KeywordsCompressor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.token_counter = MockTokenCounter({
            "short text": 5,
            "This is a very long text with important keywords": 8,
            "important keywords": 2,
        })
        self.compressor = KeywordsCompressor(self.token_counter)
    
    def test_no_compression_when_under_limit(self):
        """Test no compression when text is under token limit."""
        result = self.compressor.compress("short text", max_tokens=10, model_name="starcoder")
        
        assert result.original_text == "short text"
        assert result.compressed_text == "short text"
        assert result.compression_ratio == 1.0
        assert result.strategy_used == "no_compression"
    
    def test_keywords_extraction(self):
        """Test keywords extraction."""
        text = "This is a very long text with important keywords"
        
        result = self.compressor.compress(text, max_tokens=5, model_name="starcoder")
        
        assert result.original_text == text
        assert result.compressed_text != text
        assert result.compression_ratio < 1.0
        assert result.strategy_used == "keywords"
        # Should contain only keywords (words > 4 chars)
        words = result.compressed_text.split()
        for word in words:
            assert len(word) > 4
    
    def test_keywords_with_short_words(self):
        """Test keywords extraction with short words."""
        text = "a b c d e f g h i j k l m n o p q r s t u v w x y z"
        
        result = self.compressor.compress(text, max_tokens=5, model_name="starcoder")
        
        # Should result in empty or very short text since no words > 4 chars
        assert len(result.compressed_text.split()) <= 1
    
    def test_strategy_name(self):
        """Test strategy name."""
        assert self.compressor._get_strategy_name() == "keywords"


class TestCompressionStrategy:
    """Test CompressionStrategy enum."""
    
    def test_strategy_values(self):
        """Test strategy enum values."""
        assert CompressionStrategy.TRUNCATION.value == "truncation"
        assert CompressionStrategy.KEYWORDS.value == "keywords"
    
    def test_strategy_from_string(self):
        """Test creating strategy from string."""
        assert CompressionStrategy("truncation") == CompressionStrategy.TRUNCATION
        assert CompressionStrategy("keywords") == CompressionStrategy.KEYWORDS
    
    def test_invalid_strategy(self):
        """Test invalid strategy raises ValueError."""
        with pytest.raises(ValueError):
            CompressionStrategy("invalid")


class TestCompressionStrategyFactory:
    """Test CompressionStrategyFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.token_counter = MockTokenCounter()
    
    def test_create_truncation_strategy(self):
        """Test creating truncation strategy."""
        compressor = CompressionStrategyFactory.create(
            CompressionStrategy.TRUNCATION, 
            self.token_counter
        )
        
        assert isinstance(compressor, TruncationCompressor)
        assert compressor.token_counter == self.token_counter
    
    def test_create_keywords_strategy(self):
        """Test creating keywords strategy."""
        compressor = CompressionStrategyFactory.create(
            CompressionStrategy.KEYWORDS, 
            self.token_counter
        )
        
        assert isinstance(compressor, KeywordsCompressor)
        assert compressor.token_counter == self.token_counter
    
    def test_create_invalid_strategy(self):
        """Test creating invalid strategy raises ValueError."""
        # Create a mock strategy that's not in the factory
        class InvalidStrategy:
            value = "invalid"
        
        with pytest.raises(ValueError, match="Unsupported strategy"):
            CompressionStrategyFactory.create(InvalidStrategy(), self.token_counter)
    
    def test_get_available_strategies(self):
        """Test getting available strategies."""
        strategies = CompressionStrategyFactory.get_available_strategies()
        
        assert "truncation" in strategies
        assert "keywords" in strategies
        assert len(strategies) == 2
    
    def test_is_strategy_supported(self):
        """Test checking if strategy is supported."""
        assert CompressionStrategyFactory.is_strategy_supported("truncation")
        assert CompressionStrategyFactory.is_strategy_supported("keywords")
        assert not CompressionStrategyFactory.is_strategy_supported("invalid")
        assert not CompressionStrategyFactory.is_strategy_supported("")


class TestCompressionIntegration:
    """Integration tests for compression strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.token_counter = MockTokenCounter({
            "This is a test text with multiple sentences. It should be compressed properly. The compression should work correctly.": 20,
            "This is a test text with multiple sentences.": 8,
            "test text with multiple sentences": 5,
        })
    
    def test_truncation_vs_keywords_compression(self):
        """Test that truncation and keywords produce different results."""
        text = "This is a test text with multiple sentences. It should be compressed properly. The compression should work correctly."
        
        truncation_compressor = TruncationCompressor(self.token_counter)
        keywords_compressor = KeywordsCompressor(self.token_counter)
        
        truncation_result = truncation_compressor.compress(text, max_tokens=10, model_name="starcoder")
        keywords_result = keywords_compressor.compress(text, max_tokens=10, model_name="starcoder")
        
        # Results should be different
        assert truncation_result.compressed_text != keywords_result.compressed_text
        assert truncation_result.strategy_used == "truncation"
        assert keywords_result.strategy_used == "keywords"
        
        # Both should compress
        assert truncation_result.compression_ratio < 1.0
        assert keywords_result.compression_ratio < 1.0
    
    def test_factory_creates_different_compressors(self):
        """Test that factory creates different compressor types."""
        truncation = CompressionStrategyFactory.create(
            CompressionStrategy.TRUNCATION, 
            self.token_counter
        )
        keywords = CompressionStrategyFactory.create(
            CompressionStrategy.KEYWORDS, 
            self.token_counter
        )
        
        assert type(truncation) != type(keywords)
        assert isinstance(truncation, TruncationCompressor)
        assert isinstance(keywords, KeywordsCompressor)
