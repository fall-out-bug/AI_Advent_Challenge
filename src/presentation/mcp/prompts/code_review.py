"""MCP prompt: Dynamic code review prompts.

Following Python Zen: "Simple is better than complex."
"""


def code_review_prompt(code: str, language: str = "python", style: str = "pep8") -> str:
    """Generate dynamic code review prompt.

    Args:
        code: Code to review
        language: Programming language
        style: Style guide to check against

    Returns:
        Formatted prompt for code review
    """
    return f"""Review this {language} code following {style} guidelines:

Code:
```
{code}
```

Provide:
1. Overall quality score (0-100)
2. Issues found (categorized by severity: critical, major, minor, info)
3. Improvement suggestions
4. Security concerns
5. Performance considerations
6. Refactored code if improvements are suggested

Respond in JSON format:
{{
  "overall_score": <int>,
  "issues": [
    {{
      "severity": "critical|major|minor|info",
      "type": "<type>",
      "message": "<message>",
      "line": <line_number>,
      "suggestion": "<suggestion>"
    }}
  ],
  "suggestions": ["<suggestion1>", "<suggestion2>"],
  "compliments": ["<compliment1>"],
  "refactored_code": "<optional refactored code>"
}}"""


def code_review_prompt_simple(code: str) -> str:
    """Generate simple code review prompt.

    Args:
        code: Code to review

    Returns:
        Simple review prompt
    """
    return f"""Review this Python code and provide:
1. Overall score (0-100)
2. Main issues (max 5)
3. Top 3 suggestions

Code:
```python
{code}
```

Be concise and actionable."""
