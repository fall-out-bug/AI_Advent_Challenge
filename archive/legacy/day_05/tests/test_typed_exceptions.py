"""
Tests for typed exceptions with context.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from utils.typed_exceptions import (
    BaseTypedException,
    ErrorContext,
    ModelException,
    ModelConnectionException,
    ModelRequestException,
    ModelTimeoutException,
    ModelConfigurationException,
    ValidationException,
    BusinessLogicException,
    create_error_context
)


class TestErrorContext:
    """Test ErrorContext dataclass."""
    
    def test_error_context_creation(self):
        """Test ErrorContext creation."""
        context = ErrorContext(
            timestamp=datetime.now(),
            module="test_module",
            function="test_function",
            line_number=42,
            variables={"test_var": "test_value"}
        )
        
        assert context.module == "test_module"
        assert context.function == "test_function"
        assert context.line_number == 42
        assert context.variables == {"test_var": "test_value"}
        assert context.request_data is None
        assert context.response_data is None
        assert context.user_id is None
        assert context.session_id is None
    
    def test_error_context_with_optional_fields(self):
        """Test ErrorContext with optional fields."""
        context = ErrorContext(
            timestamp=datetime.now(),
            module="test_module",
            function="test_function",
            line_number=42,
            variables={},
            request_data={"method": "POST"},
            response_data={"status": 200},
            user_id="user123",
            session_id="session456"
        )
        
        assert context.request_data == {"method": "POST"}
        assert context.response_data == {"status": 200}
        assert context.user_id == "user123"
        assert context.session_id == "session456"


class TestBaseTypedException:
    """Test BaseTypedException functionality."""
    
    def test_base_exception_creation(self):
        """Test BaseTypedException creation."""
        exc = BaseTypedException("Test error")
        
        assert exc.message == "Test error"
        assert exc.context is not None
        assert exc.cause is None
        assert exc.traceback is not None
    
    def test_base_exception_with_context(self):
        """Test BaseTypedException with custom context."""
        context = ErrorContext(
            timestamp=datetime.now(),
            module="test_module",
            function="test_function",
            line_number=42,
            variables={}
        )
        
        exc = BaseTypedException("Test error", context)
        
        assert exc.message == "Test error"
        assert exc.context == context
    
    def test_base_exception_with_cause(self):
        """Test BaseTypedException with cause."""
        cause = ValueError("Original error")
        exc = BaseTypedException("Test error", cause=cause)
        
        assert exc.message == "Test error"
        assert exc.cause == cause
    
    def test_add_variable(self):
        """Test adding variable to context."""
        exc = BaseTypedException("Test error")
        result = exc.add_variable("test_var", "test_value")
        
        assert result is exc  # Should return self
        assert exc.context.variables["test_var"] == "test_value"
    
    def test_add_request_data(self):
        """Test adding request data."""
        exc = BaseTypedException("Test error")
        request_data = {"method": "POST", "url": "http://test.com"}
        result = exc.add_request_data(request_data)
        
        assert result is exc
        assert exc.context.request_data == request_data
    
    def test_add_response_data(self):
        """Test adding response data."""
        exc = BaseTypedException("Test error")
        response_data = {"status": 200, "data": "response"}
        result = exc.add_response_data(response_data)
        
        assert result is exc
        assert exc.context.response_data == response_data
    
    def test_add_user_context(self):
        """Test adding user context."""
        exc = BaseTypedException("Test error")
        result = exc.add_user_context("user123", "session456")
        
        assert result is exc
        assert exc.context.user_id == "user123"
        assert exc.context.session_id == "session456"
    
    def test_to_dict(self):
        """Test converting exception to dictionary."""
        exc = BaseTypedException("Test error")
        exc.add_variable("test_var", "test_value")
        
        result = exc.to_dict()
        
        assert result["type"] == "BaseTypedException"
        assert result["message"] == "Test error"
        assert "context" in result
        assert result["context"]["variables"]["test_var"] == "test_value"
        assert "traceback" in result
    
    def test_str_representation(self):
        """Test string representation."""
        exc = BaseTypedException("Test error")
        
        str_repr = str(exc)
        
        assert "BaseTypedException: Test error" in str_repr
        assert "at" in str_repr


class TestModelExceptions:
    """Test model-related exceptions."""
    
    def test_model_connection_exception(self):
        """Test ModelConnectionException."""
        exc = ModelConnectionException(
            model_name="qwen",
            url="http://localhost:8000",
            error="Connection refused"
        )
        
        assert exc.model_name == "qwen"
        assert exc.url == "http://localhost:8000"
        assert exc.error == "Connection refused"
        assert "Failed to connect to model 'qwen'" in str(exc)
    
    def test_model_request_exception_with_status(self):
        """Test ModelRequestException with status code."""
        exc = ModelRequestException(
            model_name="mistral",
            status_code=500
        )
        
        assert exc.model_name == "mistral"
        assert exc.status_code == 500
        assert "status 500" in str(exc)
    
    def test_model_request_exception_with_message(self):
        """Test ModelRequestException with error message."""
        exc = ModelRequestException(
            model_name="tinyllama",
            error_message="Invalid request format"
        )
        
        assert exc.model_name == "tinyllama"
        assert exc.error_message == "Invalid request format"
        assert "Invalid request format" in str(exc)
    
    def test_model_timeout_exception(self):
        """Test ModelTimeoutException."""
        exc = ModelTimeoutException(
            model_name="perplexity",
            timeout_seconds=30.0
        )
        
        assert exc.model_name == "perplexity"
        assert exc.timeout_seconds == 30.0
        assert "timed out after 30.0s" in str(exc)
    
    def test_model_configuration_exception(self):
        """Test ModelConfigurationException."""
        exc = ModelConfigurationException(
            model_name="chadgpt",
            config_error="API key not found"
        )
        
        assert exc.model_name == "chadgpt"
        assert exc.config_error == "API key not found"
        assert "API key not found" in str(exc)


class TestValidationException:
    """Test ValidationException."""
    
    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException(
            field_name="temperature",
            value=2.5,
            validation_rule="must be between 0.0 and 2.0"
        )
        
        assert exc.field_name == "temperature"
        assert exc.value == 2.5
        assert exc.validation_rule == "must be between 0.0 and 2.0"
        assert "temperature" in str(exc)
        assert "2.5" in str(exc)


class TestBusinessLogicException:
    """Test BusinessLogicException."""
    
    def test_business_logic_exception(self):
        """Test BusinessLogicException."""
        exc = BusinessLogicException(
            operation="switch_model",
            reason="Model not available"
        )
        
        assert exc.operation == "switch_model"
        assert exc.reason == "Model not available"
        assert "switch_model" in str(exc)
        assert "Model not available" in str(exc)


class TestCreateErrorContext:
    """Test create_error_context function."""
    
    def test_create_error_context_basic(self):
        """Test basic error context creation."""
        context = create_error_context()
        
        assert isinstance(context, ErrorContext)
        assert context.timestamp is not None
        assert context.module is not None
        assert context.function is not None
        assert context.line_number > 0
    
    def test_create_error_context_with_variables(self):
        """Test error context creation with variables."""
        variables = {"test_var": "test_value", "count": 42}
        context = create_error_context(variables=variables)
        
        assert context.variables == variables
    
    def test_create_error_context_with_data(self):
        """Test error context creation with request/response data."""
        request_data = {"method": "POST"}
        response_data = {"status": 200}
        
        context = create_error_context(
            request_data=request_data,
            response_data=response_data
        )
        
        assert context.request_data == request_data
        assert context.response_data == response_data
    
    def test_create_error_context_with_user(self):
        """Test error context creation with user context."""
        context = create_error_context(
            user_id="user123",
            session_id="session456"
        )
        
        assert context.user_id == "user123"
        assert context.session_id == "session456"


class TestExceptionChaining:
    """Test exception chaining and context building."""
    
    def test_exception_chaining(self):
        """Test chaining multiple context additions."""
        exc = ModelConnectionException(
            model_name="qwen",
            url="http://localhost:8000",
            error="Connection refused"
        )
        
        result = (exc
                 .add_variable("retry_count", 3)
                 .add_request_data({"method": "POST"})
                 .add_user_context("user123"))
        
        assert result is exc
        assert exc.context.variables["retry_count"] == 3
        assert exc.context.request_data["method"] == "POST"
        assert exc.context.user_id == "user123"
    
    def test_exception_inheritance(self):
        """Test that model exceptions inherit from base."""
        exc = ModelConnectionException(
            model_name="test",
            url="http://test.com",
            error="test error"
        )
        
        assert isinstance(exc, ModelException)
        assert isinstance(exc, BaseTypedException)
        assert isinstance(exc, Exception)
