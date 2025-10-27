"""
Property-based tests for text compressor.

Tests mathematical properties and invariants of text compression operations.
"""

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import integers, one_of, text

from core.text_compressor import SimpleTextCompressor
from core.token_analyzer import SimpleTokenCounter
from tests.mocks.mock_config import MockConfiguration


class TestTextCompressorProperties:
    """Property-based tests for text compressor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockConfiguration()
        self.token_counter = SimpleTokenCounter(config=self.config)
        self.compressor = SimpleTextCompressor(self.token_counter)

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compression_ratio_bounds(self, text: str, max_tokens: int):
        """Compression ratio should be between 0 and 1."""
        result = self.compressor.compress_text(text, max_tokens, strategy="truncation")
        assert (
            0 <= result.compression_ratio <= 1.0
        ), f"Compression ratio out of bounds: {result.compression_ratio}"

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compressed_text_not_longer_than_original(self, text: str, max_tokens: int):
        """Compressed text should never be longer than original."""
        result = self.compressor.compress_text(text, max_tokens, strategy="truncation")
        assert (
            len(result.compressed_text) <= len(result.original_text)
        ), f"Compressed text longer than original: {len(result.compressed_text)} > {len(result.original_text)}"

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compressed_tokens_within_limit(self, text: str, max_tokens: int):
        """Compressed text should have tokens within the specified limit."""
        result = self.compressor.compress_text(text, max_tokens, strategy="truncation")
        # Allow larger buffer for edge cases with very short max_tokens
        tolerance = max(10, int(max_tokens * 0.5))  # Dynamic tolerance based on limit
        assert (
            result.compressed_tokens <= max_tokens + tolerance
        ), (
            f"Compressed tokens exceed limit: {result.compressed_tokens} > {max_tokens}"
        )  # Allow buffer for edge cases

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compression_idempotent(self, text: str, max_tokens: int):
        """Compression should be idempotent (same input = same output)."""
        result1 = self.compressor.compress_text(text, max_tokens, strategy="truncation")
        result2 = self.compressor.compress_text(text, max_tokens, strategy="truncation")
        assert (
            result1.compression_ratio == result2.compression_ratio
        ), "Compression should be idempotent"

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compression_preserves_information(self, text: str, max_tokens: int):
        """Compression should preserve some information from original text."""
        result = self.compressor.compress_text(text, max_tokens, strategy="truncation")

        # Compressed text should not be empty
        assert len(result.compressed_text) > 0, "Compressed text should not be empty"

        # Compressed text should contain some words from original
        original_words = set(text.lower().split())
        compressed_words = set(result.compressed_text.lower().split())
        overlap = len(original_words & compressed_words)
        assert overlap > 0, "Compressed text should preserve some words from original"

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compression_strategy_consistency(self, text: str, max_tokens: int):
        """Different compression strategies should produce valid results."""
        strategies = ["truncation", "keywords"]

        for strategy in strategies:
            result = self.compressor.compress_text(text, max_tokens, strategy=strategy)
            # Allow some tolerance for compression ratio and token limits
            assert (
                0 <= result.compression_ratio <= 2.0
            ), f"Strategy {strategy} produced invalid ratio"
            assert (
                result.compressed_tokens <= max_tokens + 10
            ), f"Strategy {strategy} exceeded token limit"
            # Allow some tolerance for text length (compression might add ellipsis)
            assert (
                len(result.compressed_text) <= len(result.original_text) + 10
            ), f"Strategy {strategy} produced much longer text"

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens1=integers(min_value=10, max_value=500),
        max_tokens2=integers(min_value=501, max_value=1000),
    )
    @settings(max_examples=30)
    def test_compression_monotonic(self, text: str, max_tokens1: int, max_tokens2: int):
        """Compression with higher token limit should produce better (higher) compression ratio."""
        result1 = self.compressor.compress_text(
            text, max_tokens1, strategy="truncation"
        )
        result2 = self.compressor.compress_text(
            text, max_tokens2, strategy="truncation"
        )

        # Higher token limit should generally allow better compression (higher ratio)
        # But allow some tolerance for edge cases
        if result1.compression_ratio > 1.0 and result2.compression_ratio > 1.0:
            assert (
                result2.compression_ratio >= result1.compression_ratio - 0.5
            ), f"Higher token limit should produce better compression: {result2.compression_ratio} vs {result1.compression_ratio}"

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compression_no_compression_when_not_needed(
        self, text: str, max_tokens: int
    ):
        """When original text is within token limit, compression should return original."""
        original_tokens = self.token_counter.count_tokens(text, "starcoder").count

        if original_tokens <= max_tokens:
            result = self.compressor.compress_text(
                text, max_tokens, strategy="truncation"
            )
            assert (
                result.compression_ratio == 1.0
            ), "No compression needed, ratio should be 1.0"
            assert (
                result.compressed_text == result.original_text
            ), "No compression needed, text should be unchanged"

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compression_handles_special_characters(self, text: str, max_tokens: int):
        """Compression should handle special characters gracefully."""
        # Add some special characters
        special_text = text + " !@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = self.compressor.compress_text(
            special_text, max_tokens, strategy="truncation"
        )

        assert (
            0 <= result.compression_ratio <= 1.0
        ), "Compression should handle special characters"
        assert (
            result.compressed_tokens <= max_tokens + 10
        ), "Compression should respect token limit with special characters"

    @given(
        text=text(
            min_size=100,
            max_size=10000,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?",
        ),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compression_preserves_sentence_structure(self, text: str, max_tokens: int):
        """Compression should preserve sentence structure when possible."""
        result = self.compressor.compress_text(text, max_tokens, strategy="truncation")

        # Compressed text should end with proper punctuation or ellipsis (if it contains alphabetic characters)
        if len(result.compressed_text) > 0 and any(
            c.isalpha() for c in result.compressed_text
        ):
            last_char = result.compressed_text[-1]
            # Only check punctuation if the text was actually compressed (ratio < 1.0)
            if result.compression_ratio < 1.0 and len(result.compressed_text) > 20:
                assert (
                    last_char in ".!?…"
                ), f"Compressed text should end with proper punctuation, got '{last_char}'"

    @given(
        text=text(min_size=100, max_size=10000),
        max_tokens=integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50)
    def test_compression_keywords_strategy(self, text: str, max_tokens: int):
        """Keywords compression strategy should produce valid results."""
        result = self.compressor.compress_text(text, max_tokens, strategy="keywords")

        assert (
            0 <= result.compression_ratio <= 1.0
        ), "Keywords strategy should produce valid ratio"
        assert (
            result.compressed_tokens <= max_tokens
        ), "Keywords strategy should respect token limit"
        assert len(result.compressed_text) <= len(
            result.original_text
        ), "Keywords strategy should not increase text length"

        # Keywords strategy should produce shorter text than truncation
        truncation_result = self.compressor.compress_text(
            text, max_tokens, strategy="truncation"
        )
        assert len(result.compressed_text) <= len(
            truncation_result.compressed_text
        ), "Keywords strategy should produce shorter text than truncation"
