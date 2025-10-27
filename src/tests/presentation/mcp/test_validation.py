"""Tests for input validation."""
import pytest
from unittest.mock import Mock

from src.presentation.mcp.adapters.generation_adapter import GenerationAdapter
from src.presentation.mcp.adapters.review_adapter import ReviewAdapter
from src.presentation.mcp.adapters.orchestration_adapter import OrchestrationAdapter
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


class TestOrchestrationAdapterValidation:
    """Tests for orchestration adapter validation."""

    def test_validate_inputs_empty_description(self):
        """Test validation with empty description."""
        adapter = OrchestrationAdapter(Mock())
        
        with pytest.raises(MCPValidationError) as exc_info:
            adapter._validate_inputs("", "mistral", "mistral")
        
        assert exc_info.value.context["field"] == "description"

    def test_validate_inputs_empty_gen_model(self):
        """Test validation with empty generation model."""
        adapter = OrchestrationAdapter(Mock())
        
        with pytest.raises(MCPValidationError) as exc_info:
            adapter._validate_inputs(
                "Create a function", "", "mistral"
            )
        
        assert exc_info.value.context["field"] == "gen_model"

    def test_validate_inputs_empty_review_model(self):
        """Test validation with empty review model."""
        adapter = OrchestrationAdapter(Mock())
        
        with pytest.raises(MCPValidationError) as exc_info:
            adapter._validate_inputs(
                "Create a function", "mistral", ""
            )
        
        assert exc_info.value.context["field"] == "review_model"

    def test_validate_inputs_valid(self):
        """Test validation with all valid inputs."""
        adapter = OrchestrationAdapter(Mock())
        
        # Should not raise an exception
        adapter._validate_inputs(
            "Create a todo list class", "mistral", "mistral"
        )

    def test_validate_inputs_whitespace_only(self):
        """Test validation with whitespace-only inputs."""
        adapter = OrchestrationAdapter(Mock())
        
        # Description with only whitespace
        with pytest.raises(MCPValidationError):
            adapter._validate_inputs("   ", "mistral", "mistral")
        
        # Gen model with only whitespace
        with pytest.raises(MCPValidationError):
            adapter._validate_inputs("Create function", "   ", "mistral")
        
        # Review model with only whitespace
        with pytest.raises(MCPValidationError):
            adapter._validate_inputs("Create function", "mistral", "   ")
