"""Tests for enhanced token analyzer.

Following TDD approach:
- Write tests first (red)
- Implement minimal code (green)
- Refactor for clarity (refactor)
"""

from src.domain.services.token_analyzer import TokenAnalyzer


class TestEnhancedTokenAnalyzer:
    """Test enhanced token analyzer features."""

    def test_analyzer_has_model_limits(self):
        """Test that analyzer can provide model limits."""
        analyzer = TokenAnalyzer()

        limits = analyzer.get_model_limits("starcoder")

        assert limits is not None
        assert "max_input_tokens" in limits
        assert "max_output_tokens" in limits

    def test_analyzer_checks_limit_exceeded(self):
        """Test that analyzer can check if text exceeds limits."""
        analyzer = TokenAnalyzer()

        # Short text should not exceed
        short_text = "Short text"
        exceeded = analyzer.check_limit_exceeded(short_text, "starcoder")
        assert not exceeded

        # Very long text should exceed
        long_text = "word " * 10000  # ~13000 tokens
        exceeded = analyzer.check_limit_exceeded(long_text, "starcoder")
        assert exceeded

    def test_analyzer_gets_recommended_input_tokens(self):
        """Test that analyzer can recommend input token limits."""
        analyzer = TokenAnalyzer()

        recommended = analyzer.get_recommended_input_tokens("starcoder")

        assert recommended > 0
        assert isinstance(recommended, int)

    def test_analyzer_handles_unknown_model(self):
        """Test that analyzer handles unknown models gracefully."""
        analyzer = TokenAnalyzer()

        # Should not raise exception
        limits = analyzer.get_model_limits("unknown_model")
        assert limits is not None  # Should return defaults

    def test_batch_token_counting(self):
        """Test that analyzer can count tokens for multiple texts."""
        analyzer = TokenAnalyzer()

        texts = ["First text", "Second text", "Third text"]
        results = analyzer.count_tokens_batch(texts)

        assert len(results) == 3
        assert all(isinstance(count, int) for count in results)
        assert all(count > 0 for count in results)

    def test_analyzer_identifies_potential_compression(self):
        """Test that analyzer can identify when compression is recommended."""
        analyzer = TokenAnalyzer()

        # Short text - no compression needed
        short_text = "Short"
        needs_compression = analyzer.should_compress(short_text, "starcoder")
        assert not needs_compression

        # Long text - compression needed
        long_text = "word " * 5000  # ~6500 tokens
        needs_compression = analyzer.should_compress(long_text, "starcoder")
        assert needs_compression
