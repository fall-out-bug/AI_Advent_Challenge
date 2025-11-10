"""Response formatting utilities for Mistral orchestrator."""

from typing import List


def format_response(results: List[dict]) -> List[str]:
    """Format execution results."""
    parts = []
    for result in results:
        if not isinstance(result, dict):
            continue
        if "code" in result:
            parts.append(f"\nGenerated code:\n```python\n{result['code']}\n```")
        if "formatted_code" in result:
            parts.append(
                f"\nFormatted code:\n```python\n{result['formatted_code']}\n```"
            )
        if "test_code" in result:
            parts.append(f"\nGenerated tests:\n```python\n{result['test_code']}\n```")
        if "review_result" in result:
            parts.append(f"\nReview:\n{result.get('review_result', {})}")
        if "complexity" in result or "cyclomatic_complexity" in result:
            parts.append(f"\nComplexity Analysis:\n{result}")
    return parts
