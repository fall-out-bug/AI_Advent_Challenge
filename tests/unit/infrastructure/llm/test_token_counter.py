"""Unit tests for TokenCounter."""

from __future__ import annotations

import pytest

from src.infrastructure.llm.token_counter import TokenCounter


def test_count_tokens_basic():
    """Test basic token counting."""
    counter = TokenCounter(model_name="mistral")
    
    text = "This is a test sentence."
    count = counter.count_tokens(text)
    
    assert count > 0
    assert isinstance(count, int)


def test_count_tokens_empty():
    """Test counting tokens in empty text."""
    counter = TokenCounter(model_name="mistral")
    
    count = counter.count_tokens("")
    
    # Tokenizers may return 1 for empty text (special token), so allow 0-1
    assert count >= 0
    assert count <= 1


def test_count_tokens_long_text():
    """Test counting tokens in long text."""
    counter = TokenCounter(model_name="mistral")
    
    long_text = "Word " * 1000
    count = counter.count_tokens(long_text)
    
    assert count > 100  # Should be roughly proportional


def test_batch_count_tokens():
    """Test batch token counting."""
    counter = TokenCounter(model_name="mistral")
    
    texts = ["Short text.", "Another text.", "Yet another text."]
    counts = counter.batch_count_tokens(texts)
    
    assert len(counts) == len(texts)
    assert all(isinstance(c, int) and c > 0 for c in counts)


def test_count_tokens_multilingual():
    """Test counting tokens in Russian text."""
    counter = TokenCounter(model_name="mistral")
    
    russian_text = "Это тестовое предложение на русском языке."
    count = counter.count_tokens(russian_text)
    
    assert count > 0


def test_model_mapping():
    """Test that different models are handled."""
    counter_mistral = TokenCounter(model_name="mistral")
    counter_gpt = TokenCounter(model_name="gpt-4")
    
    text = "Test text"
    count_mistral = counter_mistral.count_tokens(text)
    count_gpt = counter_gpt.count_tokens(text)
    
    # Both should work, values may differ
    assert count_mistral > 0
    assert count_gpt > 0
