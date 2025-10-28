"""Response formatting utilities for Mistral orchestrator.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
"""

from typing import List


def format_code_response(results: List[dict]) -> List[str]:
    """Format code results for display.
    
    Args:
        results: List of execution results
        
    Returns:
        Formatted response parts
    """
    parts = []
    for result in results:
        if isinstance(result, dict) and 'code' in result:
            parts.append(f"\nGenerated code:\n```python\n{result['code']}\n```")
        if isinstance(result, dict) and 'formatted_code' in result:
            parts.append(f"\nFormatted code:\n```python\n{result['formatted_code']}\n```")
    return parts


def format_test_response(results: List[dict]) -> List[str]:
    """Format test results for display.
    
    Args:
        results: List of execution results
        
    Returns:
        Formatted response parts
    """
    parts = []
    for result in results:
        if isinstance(result, dict) and 'test_code' in result:
            parts.append(f"\nGenerated tests:\n```python\n{result['test_code']}\n```")
    return parts


def format_review_response(results: List[dict]) -> List[str]:
    """Format review results for display.
    
    Args:
        results: List of execution results
        
    Returns:
        Formatted response parts
    """
    parts = []
    for result in results:
        if isinstance(result, dict) and 'review_result' in result:
            parts.append(f"\nReview:\n{result.get('review_result', {})}")
    return parts


def format_complexity_response(results: List[dict]) -> List[str]:
    """Format complexity results for display.
    
    Args:
        results: List of execution results
        
    Returns:
        Formatted response parts
    """
    parts = []
    for result in results:
        if isinstance(result, dict) and ('complexity' in result or 'cyclomatic_complexity' in result):
            parts.append(f"\nComplexity Analysis:\n{result}")
    return parts

