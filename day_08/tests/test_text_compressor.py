"""
Unit tests for text compressor module.

Tests the SimpleTextCompressor class functionality including
truncation and keyword compression strategies.
"""

import pytest

from core.text_compressor import SimpleTextCompressor
from core.token_analyzer import SimpleTokenCounter
from models.data_models import CompressionResult


class TestSimpleTextCompressor:
    """Test cases for SimpleTextCompressor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.token_counter = SimpleTokenCounter()
        self.text_compressor = SimpleTextCompressor(self.token_counter)

    def test_compress_by_truncation_no_compression_needed(self):
        """Test truncation compression when no compression is needed."""
        text = "Short text"
        result = self.text_compressor.compress_by_truncation(text, 1000)

        assert result.original_text == text
        assert result.compressed_text == text
        assert result.compression_ratio == 1.0
        assert result.strategy_used == "no_compression"
        assert result.original_tokens == result.compressed_tokens

    def test_compress_by_truncation_simple_text(self):
        """Test truncation compression with simple text."""
        text = "First sentence. Second sentence. Third sentence."
        result = self.text_compressor.compress_by_truncation(text, 5)  # Very low limit

        assert result.compression_ratio < 1.0
        assert result.strategy_used == "truncation"
        assert result.compressed_tokens <= 5
        assert "First sentence" in result.compressed_text
        assert "Third sentence" in result.compressed_text

    def test_compress_by_truncation_long_text(self):
        """Test truncation compression with longer text."""
        # Create text with many sentences
        sentences = [f"This is sentence number {i}." for i in range(20)]
        text = " ".join(sentences)

        result = self.text_compressor.compress_by_truncation(text, 20)  # Low limit

        assert result.compression_ratio < 1.0
        assert result.strategy_used == "truncation"
        assert result.compressed_tokens <= 20
        assert "This is sentence number 0" in result.compressed_text
        assert "This is sentence number 19" in result.compressed_text

    def test_compress_by_keywords_no_compression_needed(self):
        """Test keyword compression when no compression is needed."""
        text = "Short text"
        result = self.text_compressor.compress_by_keywords(text, 1000)

        assert result.original_text == text
        assert result.compressed_text == text
        assert result.compression_ratio == 1.0
        assert result.strategy_used == "no_compression"

    def test_compress_by_keywords_simple_text(self):
        """Test keyword compression with simple text."""
        text = "This is a simple test with important keywords"
        result = self.text_compressor.compress_by_keywords(text, 5)  # Low limit

        assert result.compression_ratio < 1.0
        assert result.strategy_used == "keywords"
        assert result.compressed_tokens <= 5

        # Should contain keywords (words longer than 4 characters)
        compressed_words = result.compressed_text.split()
        for word in compressed_words:
            assert len(word) > 4

    def test_compress_by_keywords_long_text(self):
        """Test keyword compression with longer text."""
        text = """
        Machine learning is a fascinating field that involves algorithms and models.
        Deep learning uses neural networks with multiple layers for complex tasks.
        Natural language processing helps computers understand human language.
        Computer vision enables machines to interpret visual information.
        """

        result = self.text_compressor.compress_by_keywords(text, 10)  # Low limit

        assert result.compression_ratio < 1.0
        assert result.strategy_used == "keywords"
        assert result.compressed_tokens <= 10

        # Should contain important keywords
        compressed_text = result.compressed_text.lower()
        assert any(
            keyword in compressed_text
            for keyword in ["machine", "learning", "algorithms", "neural"]
        )

    def test_compress_text_truncation_strategy(self):
        """Test compress_text method with truncation strategy."""
        text = "First. Second. Third."
        result = self.text_compressor.compress_text(text, 5, strategy="truncation")

        assert result.strategy_used in ["truncation", "no_compression"]
        assert result.compression_ratio <= 1.0

    def test_compress_text_keywords_strategy(self):
        """Test compress_text method with keywords strategy."""
        text = "This is a test with important keywords"
        result = self.text_compressor.compress_text(text, 5, strategy="keywords")

        assert result.strategy_used == "keywords"
        assert result.compression_ratio < 1.0

    def test_compress_text_invalid_strategy(self):
        """Test compress_text method with invalid strategy."""
        text = "Some text"

        with pytest.raises(ValueError, match="Unsupported compression strategy"):
            self.text_compressor.compress_text(text, 100, strategy="invalid")

    def test_get_compression_preview(self):
        """Test compression preview functionality."""
        text = "This is a test with multiple important keywords for compression"
        preview = self.text_compressor.get_compression_preview(text, 10)

        assert "truncation" in preview
        assert "keywords" in preview

        # Check truncation preview
        truncation = preview["truncation"]
        assert "compression_ratio" in truncation
        assert "compressed_tokens" in truncation
        assert "preview" in truncation
        assert truncation["compression_ratio"] < 1.0

        # Check keywords preview
        keywords = preview["keywords"]
        assert "compression_ratio" in keywords
        assert "compressed_tokens" in keywords
        assert "preview" in keywords
        assert keywords["compression_ratio"] < 1.0

    def test_compression_preserves_meaning(self):
        """Test that compression preserves some meaning."""
        text = """
        Machine learning is a subset of artificial intelligence that focuses on algorithms.
        Deep learning uses neural networks with multiple layers to process data.
        Natural language processing helps computers understand human language.
        Computer vision enables machines to interpret and analyze visual information.
        """

        # Test truncation preserves beginning and end
        truncation_result = self.text_compressor.compress_by_truncation(text, 20)
        compressed_text = truncation_result.compressed_text.lower()

        assert "machine learning" in compressed_text
        assert "computer vision" in compressed_text

        # Test keywords preserves important terms
        keywords_result = self.text_compressor.compress_by_keywords(text, 15)
        compressed_text = keywords_result.compressed_text.lower()

        assert any(
            keyword in compressed_text
            for keyword in ["machine", "learning", "algorithms", "neural"]
        )

    def test_compression_ratio_calculation(self):
        """Test that compression ratio is calculated correctly."""
        text = "This is a test sentence with multiple words"
        result = self.text_compressor.compress_by_truncation(text, 5)

        expected_ratio = result.compressed_tokens / result.original_tokens
        assert abs(result.compression_ratio - expected_ratio) < 0.01

    def test_compression_with_different_models(self):
        """Test compression with different model configurations."""
        text = "This is a test with multiple sentences. Each sentence has different content."

        # Test with starcoder
        result_starcoder = self.text_compressor.compress_by_truncation(
            text, 10, "starcoder"
        )
        assert result_starcoder.compressed_tokens <= 10

        # Test with tinyllama
        result_tinyllama = self.text_compressor.compress_by_truncation(
            text, 10, "tinyllama"
        )
        assert result_tinyllama.compressed_tokens <= 10

    def test_compression_edge_cases(self):
        """Test compression with edge cases."""
        # Empty text
        result = self.text_compressor.compress_by_truncation("", 100)
        assert result.compression_ratio == 1.0
        assert result.strategy_used == "no_compression"

        # Single word
        result = self.text_compressor.compress_by_truncation("word", 100)
        assert result.compression_ratio == 1.0

        # Very long single word
        long_word = "supercalifragilisticexpialidocious" * 100
        result = self.text_compressor.compress_by_truncation(long_word, 10)
        assert result.compression_ratio <= 1.0

    def test_keyword_extraction_logic(self):
        """Test that keyword extraction works correctly."""
        text = "a an the this that with machine learning algorithms neural networks"

        result = self.text_compressor.compress_by_keywords(text, 5)

        # Should only contain words longer than 4 characters
        compressed_words = result.compressed_text.split()
        for word in compressed_words:
            assert len(word) > 4

        # Should contain important keywords
        assert any(
            word in result.compressed_text
            for word in ["machine", "learning", "algorithms", "neural", "networks"]
        )
