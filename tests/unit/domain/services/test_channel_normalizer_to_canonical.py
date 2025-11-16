"""Unit tests for ChannelNormalizer.to_canonical_form() method.

Purpose:
    Verify E.1 policy compliance: canonical form is lowercase without @ prefix.
"""

from __future__ import annotations

import pytest

from src.domain.services.channel_normalizer import ChannelNormalizer


class TestChannelNormalizerToCanonicalForm:
    """Test suite for to_canonical_form() method."""

    @pytest.fixture
    def normalizer(self) -> ChannelNormalizer:
        """Create ChannelNormalizer instance for tests."""
        return ChannelNormalizer()

    def test_to_canonical_form_removes_at_prefix(
        self, normalizer: ChannelNormalizer
    ) -> None:
        """Test that @ prefix is removed."""
        result = normalizer.to_canonical_form("@onaboka")
        assert result == "onaboka"

    def test_to_canonical_form_lowercase(
        self, normalizer: ChannelNormalizer
    ) -> None:
        """Test that uppercase is converted to lowercase."""
        result = normalizer.to_canonical_form("Onaboka")
        assert result == "onaboka"

    def test_to_canonical_form_removes_at_and_lowercase(
        self, normalizer: ChannelNormalizer
    ) -> None:
        """Test that @ prefix is removed and uppercase converted."""
        result = normalizer.to_canonical_form("@Onaboka")
        assert result == "onaboka"

    def test_to_canonical_form_preserves_already_canonical(
        self, normalizer: ChannelNormalizer
    ) -> None:
        """Test that already canonical form is preserved."""
        result = normalizer.to_canonical_form("onaboka")
        assert result == "onaboka"

    def test_to_canonical_form_handles_empty_string(
        self, normalizer: ChannelNormalizer
    ) -> None:
        """Test that empty string returns empty string."""
        result = normalizer.to_canonical_form("")
        assert result == ""

    def test_to_canonical_form_handles_multiple_at_prefixes(
        self, normalizer: ChannelNormalizer
    ) -> None:
        """Test that multiple @ prefixes are removed."""
        result = normalizer.to_canonical_form("@@@onaboka")
        assert result == "onaboka"

    def test_to_canonical_form_handles_whitespace(
        self, normalizer: ChannelNormalizer
    ) -> None:
        """Test that leading/trailing whitespace is removed."""
        result = normalizer.to_canonical_form("  onaboka  ")
        assert result == "onaboka"

    def test_to_canonical_form_e1_policy_compliance(
        self, normalizer: ChannelNormalizer
    ) -> None:
        """Test E.1 policy compliance: canonical form is lowercase without @ prefix."""
        test_cases = [
            ("@onaboka", "onaboka"),
            ("Onaboka", "onaboka"),
            ("ONABOKA", "onaboka"),
            ("@Onaboka", "onaboka"),
            ("onaboka", "onaboka"),
            ("  @onaboka  ", "onaboka"),
        ]

        for input_text, expected in test_cases:
            result = normalizer.to_canonical_form(input_text)
            assert result == expected, f"Input: {input_text!r}, Expected: {expected!r}, Got: {result!r}"

