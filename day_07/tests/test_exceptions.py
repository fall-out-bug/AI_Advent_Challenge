"""Tests for custom exceptions."""

import pytest

"""Tests for custom exceptions."""

import pytest

from exceptions import (
    MultiAgentError,
    CodeGenerationError,
    CodeReviewError,
    ValidationError,
    StarCoderError,
    AgentCommunicationError,
    ConfigurationError,
    RateLimitError,
)


class TestExceptions:
    """Test custom exception classes."""

    def test_multi_agent_error(self):
        """Test MultiAgentError exception."""
        error = MultiAgentError("Test multi-agent error")
        assert str(error) == "Test multi-agent error"
        assert isinstance(error, Exception)

    def test_code_generation_error(self):
        """Test CodeGenerationError exception."""
        error = CodeGenerationError("Test code generation error")
        assert str(error) == "Test code generation error"
        assert isinstance(error, MultiAgentError)

    def test_code_review_error(self):
        """Test CodeReviewError exception."""
        error = CodeReviewError("Test code review error")
        assert str(error) == "Test code review error"
        assert isinstance(error, MultiAgentError)

    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError("Test validation error")
        assert str(error) == "Test validation error"
        assert isinstance(error, MultiAgentError)

    def test_starcoder_error(self):
        """Test StarCoderError exception."""
        error = StarCoderError("Test starcoder error")
        assert str(error) == "Test starcoder error"
        assert isinstance(error, MultiAgentError)

    def test_agent_communication_error(self):
        """Test AgentCommunicationError exception."""
        error = AgentCommunicationError("Test communication error")
        assert str(error) == "Test communication error"
        assert isinstance(error, MultiAgentError)

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        error = ConfigurationError("Test configuration error")
        assert str(error) == "Test configuration error"
        assert isinstance(error, MultiAgentError)

    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        error = RateLimitError("Test rate limit error")
        assert str(error) == "Test rate limit error"
        assert isinstance(error, MultiAgentError)

    def test_exception_inheritance(self):
        """Test exception inheritance hierarchy."""
        # Test that all custom exceptions inherit from MultiAgentError
        exceptions = [
            CodeGenerationError,
            CodeReviewError,
            ValidationError,
            StarCoderError,
            AgentCommunicationError,
            ConfigurationError,
            RateLimitError,
        ]
        
        for exc_class in exceptions:
            error = exc_class("Test error")
            assert isinstance(error, MultiAgentError)
            assert isinstance(error, Exception)

    def test_exception_with_message(self):
        """Test exception with custom message."""
        error = MultiAgentError("Custom error message")
        assert str(error) == "Custom error message"

    def test_exception_without_message(self):
        """Test exception without message."""
        error = MultiAgentError()
        assert str(error) == ""
