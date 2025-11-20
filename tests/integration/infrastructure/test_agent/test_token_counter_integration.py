"""Integration tests for TokenCounter with real code samples."""

from pathlib import Path

import pytest

from src.infrastructure.test_agent.services.token_counter import TokenCounter


def test_count_tokens_real_python_module():
    """Test counting tokens in a real Python module."""
    # Arrange
    counter = TokenCounter()
    # Use a real module from the codebase
    test_file = (
        Path(__file__).parent.parent.parent.parent.parent
        / "src"
        / "domain"
        / "test_agent"
        / "entities"
        / "code_chunk.py"
    )

    if not test_file.exists():
        pytest.skip("Test file not found")

    code_content = test_file.read_text()

    # Act
    token_count = counter.count_tokens(code_content)

    # Assert
    assert isinstance(token_count, int)
    assert token_count > 0
    # Real Python module should have reasonable token count
    # (not character-based approximation if tiktoken works)
    assert token_count < len(code_content)  # Tokens should be less than characters


def test_count_tokens_matches_llm_expectations():
    """Test that token counts match GigaChat LLM expectations (reasonable range)."""
    # Arrange
    counter = TokenCounter()
    code = """
def calculate_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)

def main():
    for i in range(10):
        print(f"fib({i}) = {calculate_fibonacci(i)}")
"""

    # Act
    token_count = counter.count_tokens(code)

    # Assert
    assert isinstance(token_count, int)
    assert token_count > 0
    # For this code snippet, expect reasonable token count
    # (approximately 30-50 tokens for this code)
    assert 20 <= token_count <= 100


def test_estimate_prompt_fits_in_4000_token_limit():
    """Test that prompt size estimation works with 4000-token limit for GigaChat."""
    # Arrange
    counter = TokenCounter()
    system_prompt = "You are a test generator. Generate comprehensive unit tests."
    # Create code that should fit within 4000 tokens
    code = (
        """
def example_function(a: int, b: int) -> int:
    return a + b
"""
        * 100
    )  # Repeat to create larger code

    # Act
    estimated_size = counter.estimate_prompt_size(code, system_prompt)

    # Assert
    assert isinstance(estimated_size, int)
    assert estimated_size > 0
    # With safety buffer (90%), estimated size should account for it
    # If code + system_prompt < 3600 tokens, estimated should be < 4000
    code_tokens = counter.count_tokens(code)
    system_tokens = counter.count_tokens(system_prompt)
    total_actual = code_tokens + system_tokens

    if total_actual < 3600:
        # Estimated should be reasonable (with buffer and overhead)
        assert estimated_size <= 4000


def test_token_counter_with_large_file():
    """Test token counter with a large file."""
    # Arrange
    counter = TokenCounter()
    # Create a large code string
    large_code = (
        """
def function_{i}():
    return {i}
"""
        * 500
    )  # Create 500 functions

    # Act
    token_count = counter.count_tokens(large_code)

    # Assert
    assert isinstance(token_count, int)
    assert token_count > 0
    # Large file should have many tokens
    assert token_count > 1000
    # But tokens should be less than characters (tokenizer compresses)
    assert token_count < len(large_code)


# GigaChat tests removed - rolled back to Qwen tokenizer
