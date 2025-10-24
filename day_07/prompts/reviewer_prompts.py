"""Prompt templates for code review agent."""

from typing import List


class ReviewerPrompts:
    """Prompt templates for code review and analysis."""

    @staticmethod
    def get_code_review_prompt(
        task_description: str, generated_code: str, tests: str, metadata: dict
    ) -> str:
        """Generate prompt for comprehensive code review.

        Args:
            task_description: Original task description
            generated_code: Code to review
            tests: Test code to review
            metadata: Code metadata

        Returns:
            Formatted prompt string
        """
        return f"""You are an expert Python code reviewer. Perform a comprehensive review of the following code and tests.

ORIGINAL TASK: {task_description}

CODE TO REVIEW:
```python
{generated_code}
```

TESTS TO REVIEW:
```python
{tests}
```

METADATA:
- Complexity: {metadata.get('complexity', 'unknown')}
- Lines of Code: {metadata.get('lines_of_code', 'unknown')}
- Dependencies: {metadata.get('dependencies', [])}

REVIEW CRITERIA:
1. **Code Quality (0-10)**:
   - PEP8 compliance
   - Type hints usage
   - Docstring quality
   - Variable naming
   - Function length and complexity

2. **Functionality (0-10)**:
   - Correctness of implementation
   - Edge case handling
   - Error handling
   - Performance considerations

3. **Testing (0-10)**:
   - Test coverage
   - Test quality and clarity
   - Edge case testing
   - Error condition testing

4. **Maintainability (0-10)**:
   - Code readability
   - Modularity
   - Documentation
   - Best practices adherence

OUTPUT FORMAT:
Provide your review in the following JSON format:

```json
{{
    "overall_score": [0-10],
    "metrics": {{
        "pep8_compliance": [true/false],
        "pep8_score": [0-10],
        "has_docstrings": [true/false],
        "has_type_hints": [true/false],
        "test_coverage": "[assessment]",
        "complexity_score": [0-10]
    }},
    "issues": [
        "List specific issues found in the code"
    ],
    "recommendations": [
        "List specific recommendations for improvement"
    ]
}}
```

Be thorough, constructive, and specific in your feedback."""

    @staticmethod
    def get_pep8_analysis_prompt(code: str) -> str:
        """Generate prompt for PEP8 analysis.

        Args:
            code: Code to analyze

        Returns:
            Formatted prompt string
        """
        return f"""You are a Python style expert. Analyze the following code for PEP8 compliance.

CODE TO ANALYZE:
```python
{code}
```

ANALYSIS REQUIREMENTS:
- Check line length (max 79 characters)
- Check indentation (4 spaces)
- Check spacing around operators
- Check import organization
- Check naming conventions
- Check blank lines usage
- Check string quotes consistency

OUTPUT FORMAT:
Provide a detailed PEP8 analysis in the following format:

**PEP8 COMPLIANCE**: [COMPLIANT/NON-COMPLIANT]
**SCORE**: [0-10]

**VIOLATIONS**:
- [specific violation 1]
- [specific violation 2]

**RECOMMENDATIONS**:
- [specific fix 1]
- [specific fix 2]

Be specific about line numbers and exact issues."""

    @staticmethod
    def get_test_coverage_prompt(function_code: str, test_code: str) -> str:
        """Generate prompt for test coverage analysis.

        Args:
            function_code: Function being tested
            test_code: Test code

        Returns:
            Formatted prompt string
        """
        return f"""You are a testing expert. Analyze the test coverage for the following function and tests.

FUNCTION:
```python
{function_code}
```

TESTS:
```python
{test_code}
```

ANALYSIS REQUIREMENTS:
- Check if all code paths are tested
- Verify edge cases are covered
- Check error conditions are tested
- Assess test quality and clarity
- Identify missing test scenarios

OUTPUT FORMAT:
Provide test coverage analysis in the following format:

**COVERAGE ASSESSMENT**: [EXCELLENT/GOOD/FAIR/POOR]

**COVERED SCENARIOS**:
- [scenario 1]
- [scenario 2]

**MISSING SCENARIOS**:
- [missing scenario 1]
- [missing scenario 2]

**TEST QUALITY**: [EXCELLENT/GOOD/FAIR/POOR]
**RECOMMENDATIONS**:
- [recommendation 1]
- [recommendation 2]

Focus on practical testing improvements."""

    @staticmethod
    def get_security_analysis_prompt(code: str) -> str:
        """Generate prompt for security analysis.

        Args:
            code: Code to analyze for security issues

        Returns:
            Formatted prompt string
        """
        return f"""You are a security expert. Analyze the following Python code for potential security vulnerabilities.

CODE TO ANALYZE:
```python
{code}
```

SECURITY CHECKS:
- Input validation
- SQL injection risks
- Code injection risks
- File system access
- Network operations
- Data exposure
- Authentication/authorization
- Error handling that might leak information

OUTPUT FORMAT:
Provide security analysis in the following format:

**SECURITY LEVEL**: [SECURE/NEEDS_ATTENTION/VULNERABLE]

**POTENTIAL ISSUES**:
- [security concern 1]
- [security concern 2]

**RECOMMENDATIONS**:
- [security improvement 1]
- [security improvement 2]

Focus on practical security improvements and common Python security pitfalls."""
