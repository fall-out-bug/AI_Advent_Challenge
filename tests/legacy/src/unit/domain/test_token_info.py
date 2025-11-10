"""Tests for token info value objects."""

import pytest

from src.domain.value_objects.token_info import TokenCount, TokenInfo


def test_token_count_creation() -> None:
    """Test token count creation with valid values."""
    token_count = TokenCount(input_tokens=100, output_tokens=50, total_tokens=150)
    assert token_count.input_tokens == 100
    assert token_count.output_tokens == 50
    assert token_count.total_tokens == 150
    assert abs(token_count.ratio - 0.5) < 0.001


def test_token_count_ratio() -> None:
    """Test token count ratio calculation."""
    token_count = TokenCount(input_tokens=10, output_tokens=20, total_tokens=30)
    assert token_count.ratio == 2.0


def test_token_count_invalid_input() -> None:
    """Test token count with negative input tokens."""
    with pytest.raises(ValueError, match="cannot be negative"):
        TokenCount(input_tokens=-1, output_tokens=10, total_tokens=9)


def test_token_count_invalid_total() -> None:
    """Test token count with mismatched total."""
    with pytest.raises(ValueError, match="must equal sum"):
        TokenCount(input_tokens=10, output_tokens=10, total_tokens=30)


def test_token_info_creation() -> None:
    """Test token info creation."""
    token_count = TokenCount(input_tokens=100, output_tokens=50, total_tokens=150)
    token_info = TokenInfo(token_count=token_count, model_name="gpt-4")
    assert token_info.token_count == token_count
    assert token_info.model_name == "gpt-4"


def test_token_info_empty_model() -> None:
    """Test token info with empty model name."""
    token_count = TokenCount(input_tokens=100, output_tokens=50, total_tokens=150)
    with pytest.raises(ValueError, match="cannot be empty"):
        TokenInfo(token_count=token_count, model_name="")
