"""Tests for error handling scenarios."""

from src.presentation.mcp.exceptions import (
    MCPAgentError,
    MCPModelError,
    MCPOrchestrationError,
    MCPValidationError,
)


class TestMCPBaseException:
    """Tests for base exception class."""

    def test_exception_without_context(self):
        """Test exception with message only."""
        exc = MCPModelError("Something went wrong")

        assert str(exc) == "Something went wrong"
        assert exc.context == {}

    def test_exception_with_context(self):
        """Test exception with context."""
        context = {"model_name": "mistral", "error_code": 500}
        exc = MCPModelError("Model failed", model_name="mistral", context=context)

        assert str(exc) == "Model failed"
        assert exc.context["model_name"] == "mistral"

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        exc = MCPModelError("Test error")

        assert isinstance(exc, MCPBaseException)
        assert isinstance(exc, Exception)


class TestModelError:
    """Tests for model error handling."""

    def test_model_error_with_model_name(self):
        """Test model error includes model name in context."""
        exc = MCPModelError("Connection failed", model_name="mistral")

        assert "model_name" in exc.context
        assert exc.context["model_name"] == "mistral"

    def test_model_error_context_preserved(self):
        """Test model error preserves additional context."""
        context = {"retry_count": 3, "timeout": 5000}
        exc = MCPModelError(
            "Request timeout",
            model_name="mistral",
            context=context,
        )

        assert exc.context["model_name"] == "mistral"
        assert exc.context["retry_count"] == 3


class TestAgentError:
    """Tests for agent error handling."""

    def test_agent_error_with_agent_type(self):
        """Test agent error includes agent type."""
        exc = MCPAgentError("Processing failed", agent_type="generator")

        assert "agent_type" in exc.context
        assert exc.context["agent_type"] == "generator"

    def test_agent_error_context_merge(self):
        """Test agent error merges context correctly."""
        context = {"step": "generation"}
        exc = MCPAgentError(
            "Agent failed",
            agent_type="reviewer",
            context=context,
        )

        assert exc.context["agent_type"] == "reviewer"
        assert exc.context["step"] == "generation"


class TestOrchestrationError:
    """Tests for orchestration error handling."""

    def test_orchestration_error_with_stage(self):
        """Test orchestration error includes stage."""
        exc = MCPOrchestrationError("Workflow failed", stage="generation")

        assert "stage" in exc.context
        assert exc.context["stage"] == "generation"

    def test_orchestration_error_context(self):
        """Test orchestration error context handling."""
        context = {"attempt": 2}
        exc = MCPOrchestrationError(
            "Execution failed",
            stage="review",
            context=context,
        )

        assert exc.context["stage"] == "review"
        assert exc.context["attempt"] == 2


class TestValidationError:
    """Tests for validation error handling."""

    def test_validation_error_with_field(self):
        """Test validation error includes field."""
        exc = MCPValidationError("Invalid input", field="description")

        assert "field" in exc.context
        assert exc.context["field"] == "description"

    def test_validation_error_with_value(self):
        """Test validation error includes invalid value."""
        exc = MCPValidationError(
            "Value too long",
            field="description",
            value="A" * 1000,
        )

        assert exc.context["field"] == "description"
        assert exc.context["value"] == "A" * 1000

    def test_validation_error_context_complete(self):
        """Test validation error with all context."""
        exc = MCPValidationError(
            "Invalid input",
            field="code",
            value="",
            context={"max_length": 100},
        )

        assert exc.context["field"] == "code"
        assert exc.context["value"] == ""
        assert exc.context["max_length"] == 100
