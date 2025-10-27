"""Prompt templates for code generation agent."""

from typing import List


class GeneratorPrompts:
    """Prompt templates for code generation."""

    @staticmethod
    def get_code_generation_prompt(
        task_description: str, language: str = "python", requirements: List[str] = None
    ) -> str:
        """Generate prompt for code generation.

        Args:
            task_description: Description of the task
            language: Programming language
            requirements: Additional requirements

        Returns:
            Formatted prompt string
        """
        requirements_text = ""
        if requirements:
            requirements_text = "\n".join(f"- {req}" for req in requirements)

        return f"""You are an expert Python developer. Generate high-quality Python code based on the following task description.

TASK: {task_description}

REQUIREMENTS:
- Follow PEP8 style guide strictly
- Include comprehensive type hints for all functions
- Add detailed docstrings following Google style
- Write pytest unit tests with good coverage
- Handle edge cases and error conditions
- Use meaningful variable and function names
- Keep functions focused and under 15 lines when possible
{requirements_text}

OUTPUT FORMAT:
Please provide your response in the following exact format:

### FUNCTION
```python
[Your Python function code here]
```

### TESTS
```python
[Your pytest unit tests here]
```

### METADATA
Complexity: [low/medium/high]
Lines of Code: [number]
Dependencies: [list of required packages]
Estimated Time: [execution time estimate]

Make sure the code is production-ready and follows all Python best practices."""

    @staticmethod
    def get_test_generation_prompt(function_code: str, task_description: str) -> str:
        """Generate prompt for test generation.

        Args:
            function_code: The function to test
            task_description: Original task description

        Returns:
            Formatted prompt string
        """
        return f"""You are a testing expert. Generate comprehensive pytest unit tests for the following Python function.

FUNCTION TO TEST:
```python
{function_code}
```

ORIGINAL TASK: {task_description}

REQUIREMENTS:
- Write comprehensive pytest unit tests
- Test normal cases, edge cases, and error conditions
- Use descriptive test names
- Include fixtures where appropriate
- Test all branches and conditions
- Mock external dependencies if needed
- Ensure good test coverage

OUTPUT FORMAT:
```python
import pytest
[Your pytest tests here]
```

Focus on creating robust, maintainable tests that thoroughly validate the function's behavior."""

    @staticmethod
    def get_refinement_prompt(code: str, feedback: str) -> str:
        """Generate prompt for code refinement based on feedback.

        Args:
            code: Original code
            feedback: Feedback to incorporate

        Returns:
            Formatted prompt string
        """
        return f"""You are an expert Python developer. Refine the following code based on the provided feedback.

ORIGINAL CODE:
```python
{code}
```

FEEDBACK TO INCORPORATE:
{feedback}

REQUIREMENTS:
- Address all points in the feedback
- Maintain the original functionality
- Follow PEP8 and Python best practices
- Keep type hints and docstrings
- Ensure code remains testable

OUTPUT FORMAT:
```python
[Your refined code here]
```

Provide the improved version that addresses the feedback while maintaining code quality."""
