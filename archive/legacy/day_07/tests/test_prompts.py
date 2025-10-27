"""Tests for prompt templates."""

import pytest

from prompts.generator_prompts import GeneratorPrompts
from prompts.reviewer_prompts import ReviewerPrompts


class TestGeneratorPrompts:
    """Test generator prompt templates."""

    def test_get_code_generation_prompt_basic(self):
        """Test basic code generation prompt."""
        prompt = GeneratorPrompts.get_code_generation_prompt(
            "Create a fibonacci function"
        )
        assert "Create a fibonacci function" in prompt
        assert "REQUIREMENTS" in prompt
        assert "OUTPUT FORMAT" in prompt

    def test_get_code_generation_prompt_with_requirements(self):
        """Test code generation prompt with requirements."""
        prompt = GeneratorPrompts.get_code_generation_prompt(
            "Create a sorting algorithm",
            requirements=["Use quicksort", "Handle duplicates"],
        )
        assert "Create a sorting algorithm" in prompt
        assert "- Use quicksort" in prompt
        assert "- Handle duplicates" in prompt

    def test_get_test_generation_prompt(self):
        """Test test generation prompt."""
        function_code = "def add(a, b): return a + b"
        task_description = "Create an addition function"
        prompt = GeneratorPrompts.get_test_generation_prompt(
            function_code, task_description
        )
        assert function_code in prompt
        assert task_description in prompt
        assert "pytest unit tests" in prompt

    def test_get_refinement_prompt(self):
        """Test refinement prompt."""
        code = "def func(): pass"
        feedback = "Add docstrings"
        prompt = GeneratorPrompts.get_refinement_prompt(code, feedback)
        assert code in prompt
        assert feedback in prompt
        assert "Refine the following code" in prompt


class TestReviewerPrompts:
    """Test reviewer prompt templates."""

    def test_get_code_review_prompt(self):
        """Test code review prompt."""
        code = "def func(): pass"
        tests = "def test_func(): pass"
        metadata = {"complexity": "low", "lines_of_code": 1}
        prompt = ReviewerPrompts.get_code_review_prompt(
            "Test task", code, tests, metadata
        )
        assert code in prompt
        assert tests in prompt
        assert "expert Python code reviewer" in prompt

    def test_get_pep8_analysis_prompt(self):
        """Test PEP8 analysis prompt."""
        code = "def func(): pass"
        prompt = ReviewerPrompts.get_pep8_analysis_prompt(code)
        assert code in prompt
        assert "PEP8 compliance" in prompt

    def test_get_test_coverage_prompt(self):
        """Test test coverage prompt."""
        code = "def func(): pass"
        tests = "def test_func(): pass"
        prompt = ReviewerPrompts.get_test_coverage_prompt(code, tests)
        assert code in prompt
        assert tests in prompt
        assert "test coverage" in prompt

    def test_get_security_analysis_prompt(self):
        """Test security analysis prompt."""
        code = "def func(): pass"
        prompt = ReviewerPrompts.get_security_analysis_prompt(code)
        assert code in prompt
        assert "security vulnerabilities" in prompt
