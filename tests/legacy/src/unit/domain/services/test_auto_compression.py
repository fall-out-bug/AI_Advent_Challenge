"""Unit tests for auto-compression in TokenAnalyzer.

Following TDD principles and the Zen of Python.
"""

from src.domain.services.token_analyzer import TokenAnalyzer


class TestAnalyzeAndCompress:
    """Test analyze_and_compress method."""

    def test_no_compression_needed_short_text(self):
        """Test that short text doesn't need compression."""
        text = "This is a short test message."
        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            text, model_name="starcoder"
        )

        assert result_text == text
        assert metadata["compression_applied"] is False
        assert metadata["needs_compression"] is False

    def test_applies_compression_for_long_text(self):
        """Test that compression is applied for long text."""
        # Create a text that exceeds starcoder's limit
        long_text = " ".join(["word"] * 2000)  # ~2000 words = ~2600 tokens

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            long_text, model_name="starcoder"
        )

        assert result_text != long_text
        assert metadata["compression_applied"] is True
        assert metadata["needs_compression"] is True
        assert metadata["original_tokens"] > metadata["max_tokens"]

    def test_compression_returns_metadata(self):
        """Test that compression returns proper metadata."""
        long_text = " ".join(["test"] * 1000)

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            long_text, model_name="starcoder"
        )

        assert "original_tokens" in metadata
        assert "model_name" in metadata
        assert "max_tokens" in metadata
        assert "compression_applied" in metadata
        assert "method" in metadata

    def test_uses_truncation_strategy(self):
        """Test that truncation strategy is used by default."""
        long_text = " ".join(["word"] * 5000)  # Large enough to exceed limit

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            long_text, model_name="starcoder", strategy="truncation"
        )

        assert metadata["compression_applied"] is True
        assert len(result_text) < len(long_text)

    def test_uses_keywords_strategy(self):
        """Test that keywords strategy works."""
        long_text = " ".join(["keyword"] * 5000)  # Large enough to exceed limit

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            long_text, model_name="starcoder", strategy="keywords"
        )

        assert metadata["compression_applied"] is True
        assert len(result_text.split()) <= len(long_text.split())

    def test_auto_strategy_defaults_to_truncation(self):
        """Test that auto strategy defaults to truncation."""
        long_text = " ".join(["word"] * 5000)  # Large enough to exceed limit

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            long_text, model_name="starcoder", strategy="auto"
        )

        assert metadata["compression_applied"] is True
        assert len(result_text) < len(long_text)

    def test_works_with_different_models(self):
        """Test that compression works with different models."""
        long_text = " ".join(["word"] * 1000)

        # Test with different models
        for model in ["starcoder", "mistral", "qwen"]:
            result_text, metadata = TokenAnalyzer.analyze_and_compress(
                long_text, model_name=model
            )

            assert metadata["model_name"] == model
            assert "max_tokens" in metadata


class TestCompressionScenarios:
    """Test different compression scenarios."""

    def test_edge_case_empty_text(self):
        """Test handling of empty text."""
        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            "", model_name="starcoder"
        )

        assert result_text == ""
        assert metadata["compression_applied"] is False

    def test_edge_case_very_long_text(self):
        """Test handling of very long text."""
        very_long_text = " ".join(["word"] * 5000)

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            very_long_text, model_name="starcoder"
        )

        assert len(result_text) < len(very_long_text)
        assert metadata["compression_applied"] is True

    def test_compression_ratio_calculation(self):
        """Test compression ratio calculation."""
        long_text = " ".join(["word"] * 1000)

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            long_text, model_name="starcoder"
        )

        assert "compression_ratio" in metadata
        assert 0 < metadata["compression_ratio"] <= 1.0


class TestCompressionMetadata:
    """Test compression metadata."""

    def test_metadata_includes_all_fields(self):
        """Test that metadata includes all required fields."""
        long_text = " ".join(["word"] * 1000)

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            long_text, model_name="mistral"
        )

        required_fields = [
            "original_tokens",
            "model_name",
            "max_tokens",
            "needs_compression",
            "compression_applied",
            "method",
            "compression_ratio",
        ]

        for field in required_fields:
            assert field in metadata, f"Missing field: {field}"

    def test_metadata_for_no_compression(self):
        """Test metadata when compression is not applied."""
        short_text = "Short text"

        result_text, metadata = TokenAnalyzer.analyze_and_compress(
            short_text, model_name="starcoder"
        )

        assert metadata["compression_applied"] is False
        assert metadata["needs_compression"] is False
        assert metadata["method"] is None
        assert metadata["compression_ratio"] == 1.0
