"""
Unit tests for token analyzer module.

Tests the SimpleTokenCounter class functionality including
token counting, limit checking, and model configuration.
"""

import pytest

from core.token_analyzer import LimitProfile, SimpleTokenCounter
from models.data_models import ModelLimits, TokenInfo
from tests.mocks import MockConfiguration


class TestSimpleTokenCounter:
    """Test cases for SimpleTokenCounter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = MockConfiguration()
        self.token_counter = SimpleTokenCounter(config=self.mock_config)

    def test_count_tokens_empty_text(self):
        """Test token counting with empty text."""
        result = self.token_counter.count_tokens("")
        assert result.count == 0
        assert result.model_name == "starcoder"
        assert result.estimated_cost == 0.0

    def test_count_tokens_simple_text(self):
        """Test token counting with simple text."""
        text = "Hello world"
        result = self.token_counter.count_tokens(text)

        # Should be approximately 1.3 tokens per word
        expected_tokens = int(len(text.split()) * 1.3)
        assert result.count == expected_tokens
        assert result.count == 2  # "Hello world" = 2 words * 1.3 = 2 tokens

    def test_count_tokens_long_text(self):
        """Test token counting with longer text."""
        text = "This is a longer text with multiple words to test token counting"
        result = self.token_counter.count_tokens(text)

        word_count = len(text.split())
        expected_tokens = int(word_count * 1.3)
        assert result.count == expected_tokens
        assert result.count == 15  # 12 words * 1.3 = 15 tokens

    def test_count_tokens_different_model(self):
        """Test token counting with different model name."""
        text = "Test text"
        result = self.token_counter.count_tokens(text, "mistral")

        assert result.model_name == "mistral"
        assert result.count == 2  # 2 words * 1.3 = 2 tokens

    def test_get_model_limits_starcoder(self):
        """Test getting limits for StarCoder model."""
        limits = self.token_counter.get_model_limits("starcoder")

        # Should use practical limits (4096) by default
        assert limits.max_input_tokens == 4096
        assert limits.max_output_tokens == 1024
        assert limits.max_total_tokens == 6000

    def test_get_model_limits_tinyllama(self):
        """Test getting limits for TinyLlama model."""
        limits = self.token_counter.get_model_limits("tinyllama")

        assert limits.max_input_tokens == 2048
        assert limits.max_output_tokens == 512
        assert limits.max_total_tokens == 2048

    def test_get_model_limits_unknown_model(self):
        """Test getting limits for unknown model (should default to starcoder)."""
        limits = self.token_counter.get_model_limits("unknown_model")

        # Should default to starcoder practical limits
        assert limits.max_input_tokens == 4096
        assert limits.max_output_tokens == 1024

    def test_check_limit_exceeded_within_limit(self):
        """Test limit checking with text within limits."""
        text = "Short text"
        exceeds = self.token_counter.check_limit_exceeded(text, "starcoder")

        assert not exceeds

    def test_check_limit_exceeded_over_limit(self):
        """Test limit checking with text over limits."""
        # Create text that exceeds starcoder limit (8192 tokens)
        # Need approximately 6300+ words to exceed limit
        text = "word " * 7000  # 7000 words * 1.3 = 9100 tokens > 8192
        exceeds = self.token_counter.check_limit_exceeded(text, "starcoder")

        assert exceeds

    def test_check_limit_exceeded_tinyllama(self):
        """Test limit checking with TinyLlama model."""
        # Create text that exceeds tinyllama limit (2048 tokens)
        text = "word " * 2000  # 2000 words * 1.3 = 2600 tokens > 2048
        exceeds = self.token_counter.check_limit_exceeded(text, "tinyllama")

        assert exceeds

    def test_get_available_models(self):
        """Test getting list of available models."""
        models = self.token_counter.get_available_models()

        assert "starcoder" in models
        assert "mistral" in models
        assert "qwen" in models
        assert "tinyllama" in models
        assert len(models) == 4

    def test_estimate_compression_target(self):
        """Test compression target estimation."""
        text = "Some text"
        target = self.token_counter.estimate_compression_target(text, "starcoder", 0.9)

        limits = self.token_counter.get_model_limits("starcoder")
        expected_target = int(limits.max_input_tokens * 0.9)

        assert target == expected_target
        assert target == int(4096 * 0.9)  # 3686

    def test_estimate_compression_target_different_safety_margin(self):
        """Test compression target with different safety margin."""
        text = "Some text"
        target = self.token_counter.estimate_compression_target(text, "starcoder", 0.8)

        limits = self.token_counter.get_model_limits("starcoder")
        expected_target = int(limits.max_input_tokens * 0.8)

        assert target == expected_target
        assert target == int(4096 * 0.8)  # 3276

    def test_token_counting_accuracy(self):
        """Test that token counting is within expected accuracy."""
        test_cases = [
            ("Hello", 1),
            ("Hello world", 2),
            ("This is a test", 4),
            ("Machine learning is fascinating", 4),
        ]

        for text, expected_words in test_cases:
            result = self.token_counter.count_tokens(text)
            expected_tokens = int(expected_words * 1.3)

            assert result.count == expected_tokens
            assert abs(result.count - expected_words * 1.3) < 1  # Within 1 token

    def test_model_limits_consistency(self):
        """Test that model limits are consistent."""
        for model_name in self.token_counter.get_available_models():
            limits = self.token_counter.get_model_limits(model_name)

            # Total tokens should be at least as much as input tokens
            assert limits.max_total_tokens >= limits.max_input_tokens

            # Output tokens should be reasonable
            assert limits.max_output_tokens > 0
            assert limits.max_output_tokens <= limits.max_input_tokens
