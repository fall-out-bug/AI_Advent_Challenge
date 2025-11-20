"""Tests for compression service.

Following TDD approach:
- Write tests first (red)
- Implement minimal code (green)
- Refactor for clarity (refactor)
"""

from src.domain.services.compression.strategies.keyword_compressor import (
    KeywordCompressor,
)
from src.domain.services.compression.strategies.truncation_compressor import (
    TruncationCompressor,
)
from src.domain.services.token_analyzer import TokenAnalyzer


class TestCompressionService:
    """Test compression service interface."""

    def test_truncation_compressor_initialization(self):
        """Test that compressor can be initialized."""
        token_analyzer = TokenAnalyzer()
        compressor = TruncationCompressor(token_analyzer)

        assert compressor is not None
        assert compressor.token_analyzer == token_analyzer

    def test_should_compress_when_text_exceeds_limit(self):
        """Test compression decision when text is too long."""
        token_analyzer = TokenAnalyzer()
        compressor = TruncationCompressor(token_analyzer)

        # Long text (300 words approx 390 tokens)
        long_text = "word " * 300

        result = compressor.compress(long_text, max_tokens=100)

        assert result.compression_ratio.ratio < 1.0
        assert result.original_tokens > result.compressed_tokens

    def test_should_not_compress_when_text_within_limit(self):
        """Test that short text is not compressed."""
        token_analyzer = TokenAnalyzer()
        compressor = TruncationCompressor(token_analyzer)

        short_text = "Short text that fits within limits."

        result = compressor.compress(short_text, max_tokens=100)

        assert result.compression_ratio.ratio == 1.0
        assert result.original_text == result.compressed_text

    def test_compression_preserves_first_sentence(self):
        """Test that compression preserves first sentence."""
        token_analyzer = TokenAnalyzer()
        compressor = TruncationCompressor(token_analyzer)

        text = "First sentence. Second sentence. Third sentence."
        # Force compression by setting very low limit
        result = compressor.compress(text, max_tokens=5)

        assert "First" in result.compressed_text
        assert result.compression_ratio.ratio < 1.0

    def test_compression_preserves_last_sentence(self):
        """Test that compression preserves last sentence."""
        token_analyzer = TokenAnalyzer()
        compressor = TruncationCompressor(token_analyzer)

        text = "First sentence. Second sentence. Third sentence."
        # Force compression
        result = compressor.compress(text, max_tokens=5)

        assert "Third" in result.compressed_text
        assert result.compression_ratio.ratio < 1.0

    def test_keyword_compressor_extracts_keywords(self):
        """Test that keyword compressor extracts important words."""
        token_analyzer = TokenAnalyzer()
        compressor = KeywordCompressor(token_analyzer)

        text = "This is a very important sentence with significant content."
        result = compressor.compress(text, max_tokens=10)

        # Should extract words longer than 4 chars
        assert "important" in result.compressed_text
        assert "sentence" in result.compressed_text
        assert result.compression_ratio.ratio < 1.0

    def test_keyword_compressor_skips_short_words(self):
        """Test that keyword compressor skips short words."""
        token_analyzer = TokenAnalyzer()
        compressor = KeywordCompressor(token_analyzer)

        text = "This is a very important sentence."
        result = compressor.compress(text, max_tokens=10)

        # Short words should be filtered out
        compressed_words = result.compressed_text.split()
        assert "This" not in compressed_words
        assert "very" not in compressed_words
