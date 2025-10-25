"""
Property-based tests for token analyzer.

Tests mathematical properties and invariants of token counting operations.
"""

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import integers, one_of, text

from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration


class TestTokenAnalyzerProperties:
    """Property-based tests for token analyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockConfiguration()
        self.counter = SimpleTokenCounter(config=self.config)

    @given(text=text(min_size=1, max_size=10000))
    @settings(max_examples=100)
    def test_token_count_non_negative(self, text: str):
        """Token count should always be non-negative."""
        result = self.counter.count_tokens(text, "starcoder")
        assert (
            result.count >= 0
        ), f"Token count should be non-negative, got {result.count}"

    @given(text=text(min_size=1, max_size=10000))
    @settings(max_examples=100)
    def test_token_count_proportional_to_length(self, text: str):
        """Token count should be roughly proportional to text length."""
        result = self.counter.count_tokens(text, "starcoder")
        word_count = len(text.split())

        # Skip if no words (empty or only whitespace)
        if word_count == 0:
            assert result.count == 0
            return

        # Heuristic: tokens ≈ words * 1.3, with reasonable bounds
        assert (
            result.count <= word_count * 3
        ), f"Token count too high: {result.count} > {word_count * 3}"
        assert result.count >= max(
            1, word_count // 3
        ), f"Token count too low: {result.count} < {word_count // 3}"

    @given(text=text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_token_count_idempotent(self, text: str):
        """Token count should be idempotent (same input = same output)."""
        result1 = self.counter.count_tokens(text, "starcoder")
        result2 = self.counter.count_tokens(text, "starcoder")
        assert result1.count == result2.count, "Token counting should be idempotent"

    @given(text1=text(min_size=1, max_size=1000), text2=text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_token_count_additive(self, text1: str, text2: str):
        """Token count should be roughly additive for concatenated text."""
        result1 = self.counter.count_tokens(text1, "starcoder")
        result2 = self.counter.count_tokens(text2, "starcoder")
        combined_result = self.counter.count_tokens(text1 + " " + text2, "starcoder")

        # Combined count should be close to sum of individual counts
        individual_sum = result1.count + result2.count
        assert (
            combined_result.count <= individual_sum + 5
        ), f"Combined count too high: {combined_result.count} > {individual_sum + 5}"
        assert (
            combined_result.count >= individual_sum - 5
        ), f"Combined count too low: {combined_result.count} < {individual_sum - 5}"

    @given(text=text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_token_count_case_sensitive(self, text: str):
        """Token count may vary with case changes."""
        upper_text = text.upper()
        lower_text = text.lower()

        upper_result = self.counter.count_tokens(upper_text, "starcoder")
        lower_result = self.counter.count_tokens(lower_text, "starcoder")

        # Case changes may affect token count, but shouldn't be dramatically different
        ratio = abs(upper_result.count - lower_result.count) / max(
            upper_result.count, lower_result.count, 1
        )
        assert ratio <= 0.5, f"Case change caused dramatic token count change: {ratio}"

    @given(
        text=text(min_size=1, max_size=1000),
        model=one_of(
            st.just("starcoder"),
            st.just("mistral"),
            st.just("qwen"),
            st.just("tinyllama"),
        ),
    )
    @settings(max_examples=50)
    def test_token_count_model_consistent(self, text: str, model: str):
        """Token count should be consistent across different models."""
        result = self.counter.count_tokens(text, model)
        assert (
            result.count >= 0
        ), f"Token count should be non-negative for model {model}"
        assert (
            result.count <= len(text) * 2
        ), f"Token count too high for model {model}: {result.count}"

    @given(text=text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_token_count_whitespace_insensitive(self, text: str):
        """Token count should be relatively insensitive to whitespace changes."""
        # Normalize whitespace
        normalized_text = " ".join(text.split())
        result1 = self.counter.count_tokens(text, "starcoder")
        result2 = self.counter.count_tokens(normalized_text, "starcoder")

        # Counts should be similar (within 20% difference)
        if result1.count > 0 and result2.count > 0:
            ratio = abs(result1.count - result2.count) / max(
                result1.count, result2.count
            )
            assert (
                ratio <= 0.2
            ), f"Whitespace normalization caused significant change: {ratio}"

    @given(text=text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_token_count_punctuation_aware(self, text: str):
        """Token count should be aware of punctuation."""
        # Remove punctuation
        no_punct = "".join(c for c in text if c.isalnum() or c.isspace())
        result1 = self.counter.count_tokens(text, "starcoder")
        result2 = self.counter.count_tokens(no_punct, "starcoder")

        # Punctuation removal may change count, but not dramatically
        if result1.count > 0 and result2.count > 0:
            ratio = abs(result1.count - result2.count) / max(
                result1.count, result2.count
            )
            assert ratio <= 0.5, f"Punctuation removal caused dramatic change: {ratio}"

    @given(text=text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_token_count_empty_string_handling(self, text: str):
        """Empty string should return 0 tokens."""
        if not text.strip():
            result = self.counter.count_tokens(text, "starcoder")
            assert (
                result.count == 0
            ), f"Empty string should return 0 tokens, got {result.count}"

    @given(text=text(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_token_count_repeated_text(self, text: str):
        """Repeated text should have proportional token count."""
        if text.strip():
            repeated_text = text * 3
            result1 = self.counter.count_tokens(text, "starcoder")
            result2 = self.counter.count_tokens(repeated_text, "starcoder")

            # Repeated text should have roughly 3x the tokens
            if result1.count > 0:
                ratio = result2.count / result1.count
                # Allow more flexibility for edge cases
                assert 1.0 <= ratio <= 4.0, f"Repeated text ratio unexpected: {ratio}"
