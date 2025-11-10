"""Tests for input validation."""
from unittest.mock import Mock

import pytest

from src.presentation.mcp.adapters.generation_adapter import GenerationAdapter
from src.presentation.mcp.adapters.review_adapter import ReviewAdapter
from src.presentation.mcp.exceptions import MCPValidationError


class TestGenerationAdapterValidation:
    """Tests for generation adapter validation."""

    def test_validate_description_empty_string(self):
        """Test validation with empty description."""
        adapter = GenerationAdapter(Mock(), model_name="mistral")

        with pytest.raises(MCPValidationError) as exc_info:
            adapter._validate_description("")

        assert exc_info.value.context["field"] == "description"

    def test_validate_description_whitespace_only(self):
        """Test validation with whitespace-only description."""
        adapter = GenerationAdapter(Mock(), model_name="mistral")

        with pytest.raises(MCPValidationError) as exc_info:
            adapter._validate_description("   \n\t   ")

        assert exc_info.value.context["field"] == "description"

    def test_validate_description_valid(self):
        """Test validation with valid description."""
        adapter = GenerationAdapter(Mock(), model_name="mistral")

        # Should not raise an exception
        adapter._validate_description("Create a function to calculate fibonacci")


class TestReviewAdapterValidation:
    """Tests for review adapter validation."""

    def test_validate_code_empty_string(self):
        """Test validation with empty code."""
        adapter = ReviewAdapter(Mock(), model_name="mistral")

        with pytest.raises(MCPValidationError) as exc_info:
            adapter._validate_code("")

        assert exc_info.value.context["field"] == "code"

    def test_validate_code_whitespace_only(self):
        """Test validation with whitespace-only code."""
        adapter = ReviewAdapter(Mock(), model_name="mistral")

        with pytest.raises(MCPValidationError) as exc_info:
            adapter._validate_code("   \n\t   ")

        assert exc_info.value.context["field"] == "code"

    def test_validate_code_valid(self):
        """Test validation with valid code."""
        adapter = ReviewAdapter(Mock(), model_name="mistral")
        code = """def hello():
    print("world")
"""
        # Should not raise an exception
        adapter._validate_code(code)
