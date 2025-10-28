"""MCP prompt: Dynamic test generation prompts.

Following Python Zen: "Simple is better than complex."
"""

from typing import Any


def test_generation_prompt(code: str, framework: str = "pytest") -> str:
    """Generate dynamic test generation prompt.
    
    Args:
        code: Code to generate tests for
        framework: Testing framework
        
    Returns:
        Formatted prompt for test generation
    """
    return f"""Generate comprehensive {framework} tests for this code:

{code}

Include:
- Unit tests for all functions
- Edge case testing
- Error handling tests
- Integration tests where applicable
- Mocking for external dependencies
- Docstrings for each test
- Clear test names describing the scenario

Target: 80%+ code coverage

Return ONLY the test code, no markdown formatting."""


def test_generation_prompt_simple(code: str) -> str:
    """Generate simple test prompt.
    
    Args:
        code: Code to test
        
    Returns:
        Simple test generation prompt
    """
    return f"""Write pytest tests for this code:

{code}

Include 3-5 test cases covering main functionality and edge cases.
Return test code only."""

