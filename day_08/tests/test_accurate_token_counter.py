"""
Tests for accurate token counter using HuggingFace tokenizers.
"""

import pytest

from core.accurate_token_counter import AccurateTokenCounter
from models.data_models import TokenInfo


@pytest.fixture
def accurate_counter():
    """Create AccurateTokenCounter instance."""
    return AccurateTokenCounter()


def test_count_tokens_empty_text(accurate_counter):
    """Test token counting with empty text."""
    result = accurate_counter.count_tokens("", "starcoder")
    assert result.count == 0
    assert result.model_name == "starcoder"


def test_count_tokens_simple_text(accurate_counter):
    """Test token counting with simple text."""
    text = "Hello world"
    result = accurate_counter.count_tokens(text, "starcoder")

    # Should be more accurate than simple estimation
    assert result.count > 0
    assert result.count <= 10  # Should be reasonable
    assert result.model_name == "starcoder"


def test_count_tokens_long_text(accurate_counter):
    """Test token counting with longer text."""
    text = "This is a longer text with multiple words to test accurate token counting"
    result = accurate_counter.count_tokens(text, "starcoder")

    assert result.count > 0
    assert result.model_name == "starcoder"


def test_get_available_models(accurate_counter):
    """Test getting available model names."""
    models = accurate_counter.get_available_models()

    assert "starcoder" in models
    assert "mistral" in models
    assert "qwen" in models
    assert "tinyllama" in models


def test_add_model(accurate_counter):
    """Test adding a new model."""
    accurate_counter.add_model("test_model", "test/model-id")

    models = accurate_counter.get_available_models()
    assert "test_model" in models


def test_clear_cache(accurate_counter):
    """Test clearing tokenizer cache."""
    # This should not raise an exception
    accurate_counter.clear_cache()


def test_unsupported_model(accurate_counter):
    """Test behavior with unsupported model."""
    result = accurate_counter.count_tokens("test", "unsupported_model")

    # Should fallback to simple estimation
    assert result.count > 0
    assert result.model_name == "unsupported_model"


def test_tokenizer_caching(accurate_counter):
    """Test that tokenizers are cached properly."""
    # First call should load tokenizer
    result1 = accurate_counter.count_tokens("test", "starcoder")

    # Second call should use cached tokenizer
    result2 = accurate_counter.count_tokens("test", "starcoder")

    # Results should be identical
    assert result1.count == result2.count
