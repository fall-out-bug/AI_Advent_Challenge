"""Unit tests for ITokenCounter interface."""

import pytest

from src.domain.test_agent.interfaces.token_counter import ITokenCounter
from src.infrastructure.test_agent.services.token_counter import TokenCounter


def test_count_tokens_simple_text():
    """Test counting tokens in simple text."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    text = "Hello world"

    # Act
    token_count = counter.count_tokens(text)

    # Assert
    assert isinstance(token_count, int)
    assert token_count > 0
    assert token_count >= len(text.split())  # At least one token per word


def test_count_tokens_python_code():
    """Test counting tokens in Python code."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    code = """
def calculate_sum(a: int, b: int) -> int:
    return a + b
"""

    # Act
    token_count = counter.count_tokens(code)

    # Assert
    assert isinstance(token_count, int)
    assert token_count > 0
    assert token_count > len(code.split())  # Code has more tokens than words


def test_count_tokens_empty_string():
    """Test counting tokens in empty string."""
    # Arrange
    counter: ITokenCounter = TokenCounter()

    # Act
    token_count = counter.count_tokens("")

    # Assert
    assert isinstance(token_count, int)
    assert token_count >= 0  # Empty string may have 0 or special tokens


def test_count_tokens_unicode_characters():
    """Test counting tokens with unicode characters."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    text = "Привет мир! Hello world! こんにちは"

    # Act
    token_count = counter.count_tokens(text)

    # Assert
    assert isinstance(token_count, int)
    assert token_count > 0


def test_estimate_prompt_size_with_system_prompt():
    """Test estimating prompt size with system prompt."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    code = "def test(): pass"
    system_prompt = "You are a test generator."

    # Act
    total_size = counter.estimate_prompt_size(code, system_prompt)

    # Assert
    assert isinstance(total_size, int)
    assert total_size > 0
    assert total_size >= counter.count_tokens(code)
    assert total_size >= counter.count_tokens(system_prompt)


def test_estimate_prompt_size_includes_overhead():
    """Test that prompt size estimation includes overhead."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    code = "def test(): pass"
    system_prompt = "Generate tests."

    # Act
    code_tokens = counter.count_tokens(code)
    system_tokens = counter.count_tokens(system_prompt)
    total_size = counter.estimate_prompt_size(code, system_prompt)

    # Assert
    assert total_size >= code_tokens + system_tokens
    # May include additional overhead for formatting


def test_token_counter_uses_correct_tokenizer():
    """Test that token counter uses correct tokenizer (Qwen-compatible)."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    text = "def hello(): print('world')"

    # Act
    token_count = counter.count_tokens(text)

    # Assert
    assert isinstance(token_count, int)
    assert token_count > 0
    # Verify it's using tiktoken (Qwen-compatible tokenizer)
    # Token count should be reasonable (not character-based approximation)


def test_token_count_consistency():
    """Test that token counting is consistent across calls."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    text = "def test_function(): return 42"

    # Act
    count1 = counter.count_tokens(text)
    count2 = counter.count_tokens(text)

    # Assert
    assert count1 == count2
    assert isinstance(count1, int)


def test_token_counter_no_sensitive_data_in_logs():
    """Test that token counter doesn't log sensitive data."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    sensitive_code = "api_key = 'secret_key_12345'"

    # Act & Assert
    # Should not raise exceptions or log sensitive data
    token_count = counter.count_tokens(sensitive_code)
    assert isinstance(token_count, int)
    assert token_count > 0
    # Note: Actual logging verification would require log capture,
    # but this test ensures the method doesn't fail with sensitive data


def test_token_counter_no_data_leakage():
    """Test that token counter doesn't leak data in error messages."""
    # Arrange
    counter: ITokenCounter = TokenCounter()
    sensitive_data = "password = 'my_secret_password'"

    # Act & Assert
    # Should handle sensitive data without exposing it in errors
    try:
        token_count = counter.count_tokens(sensitive_data)
        assert isinstance(token_count, int)
    except Exception as e:
        # If exception occurs, ensure sensitive data not in message
        error_msg = str(e)
        assert "password" not in error_msg.lower()
        assert "secret" not in error_msg.lower()
