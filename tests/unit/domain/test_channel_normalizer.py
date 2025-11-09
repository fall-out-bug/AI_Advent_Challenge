"""Unit tests for ChannelNormalizer service.

Following TDD: tests written first before implementation.
"""

from __future__ import annotations

import pytest

from src.domain.services.channel_normalizer import ChannelNormalizer


class TestChannelNormalizer:
    """Test suite for ChannelNormalizer."""

    def test_normalize_lowercase(self) -> None:
        """Test normalization converts to lowercase."""
        normalizer = ChannelNormalizer()
        result = normalizer.normalize("HELLO WORLD")
        assert result == "hello world"

    def test_normalize_removes_punctuation(self) -> None:
        """Test normalization removes punctuation."""
        normalizer = ChannelNormalizer()
        result = normalizer.normalize("Hello, World!")
        assert result == "hello world"

    def test_normalize_handles_dashes(self) -> None:
        """Test normalization handles dashes and hyphens."""
        normalizer = ChannelNormalizer()
        result1 = normalizer.normalize("large-caliber")
        result2 = normalizer.normalize("large–caliber")  # en dash
        result3 = normalizer.normalize("large—caliber")  # em dash
        assert result1 == "large caliber"
        assert result2 == "large caliber"
        assert result3 == "large caliber"

    def test_normalize_removes_extra_spaces(self) -> None:
        """Test normalization removes extra spaces."""
        normalizer = ChannelNormalizer()
        result = normalizer.normalize("hello    world")
        assert result == "hello world"

    def test_tokenize_simple(self) -> None:
        """Test tokenization of simple text."""
        normalizer = ChannelNormalizer()
        result = normalizer.tokenize("hello world")
        assert result == ["hello", "world"]

    def test_tokenize_with_punctuation(self) -> None:
        """Test tokenization removes punctuation."""
        normalizer = ChannelNormalizer()
        result = normalizer.tokenize("hello, world!")
        assert result == ["hello", "world"]

    def test_transliterate_ru_to_lat(self) -> None:
        """Test Russian to Latin transliteration."""
        normalizer = ChannelNormalizer()
        result = normalizer.transliterate_ru_to_lat("Набока")
        assert result == "naboka"

    def test_transliterate_lat_to_ru(self) -> None:
        """Test Latin to Russian transliteration."""
        normalizer = ChannelNormalizer()
        result = normalizer.transliterate_lat_to_ru("naboka")
        # Should attempt transliteration (may not be perfect)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_normalize_handles_cyrillic(self) -> None:
        """Test normalization handles Cyrillic text."""
        normalizer = ChannelNormalizer()
        result = normalizer.normalize("Набока орёт в борщ")
        assert "набока" in result
        assert "орёт" in result.lower()

    def test_transliterate_handles_unicode(self) -> None:
        """Test transliteration handles Unicode characters."""
        normalizer = ChannelNormalizer()
        result = normalizer.transliterate_ru_to_lat("Крупнокалиберный")
        assert result == "krupnokalibernyj"

    def test_tokenize_handles_cyrillic(self) -> None:
        """Test tokenization handles Cyrillic text."""
        normalizer = ChannelNormalizer()
        result = normalizer.tokenize("Набока орёт")
        assert "набока" in result
        assert "орёт" in result

    def test_normalize_preserves_essential_words(self) -> None:
        """Test normalization preserves essential words."""
        normalizer = ChannelNormalizer()
        result = normalizer.normalize("XOR Journal")
        assert "xor" in result
        assert "journal" in result

    def test_tokenize_empty_string(self) -> None:
        """Test tokenization of empty string."""
        normalizer = ChannelNormalizer()
        result = normalizer.tokenize("")
        assert result == []

    def test_normalize_empty_string(self) -> None:
        """Test normalization of empty string."""
        normalizer = ChannelNormalizer()
        result = normalizer.normalize("")
        assert result == ""
