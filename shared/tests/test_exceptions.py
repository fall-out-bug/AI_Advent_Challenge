"""
Tests for shared.exceptions.model_errors module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest
from shared_package.exceptions.model_errors import (
    ModelClientError,
    ModelConfigurationError,
    ModelConnectionError,
    ModelNotAvailableError,
    ModelRequestError,
    ModelTimeoutError,
)


class TestModelExceptions:
    """Test model exception classes."""

    def test_model_client_error_inheritance(self):
        """Test ModelClientError inheritance."""
        error = ModelClientError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_model_connection_error_inheritance(self):
        """Test ModelConnectionError inheritance."""
        error = ModelConnectionError("Connection failed")
        assert isinstance(error, ModelClientError)
        assert isinstance(error, Exception)
        assert str(error) == "Connection failed"

    def test_model_request_error_inheritance(self):
        """Test ModelRequestError inheritance."""
        error = ModelRequestError("Request failed")
        assert isinstance(error, ModelClientError)
        assert isinstance(error, Exception)
        assert str(error) == "Request failed"

    def test_model_timeout_error_inheritance(self):
        """Test ModelTimeoutError inheritance."""
        error = ModelTimeoutError("Request timed out")
        assert isinstance(error, ModelClientError)
        assert isinstance(error, Exception)
        assert str(error) == "Request timed out"

    def test_model_configuration_error_inheritance(self):
        """Test ModelConfigurationError inheritance."""
        error = ModelConfigurationError("Invalid configuration")
        assert isinstance(error, ModelClientError)
        assert isinstance(error, Exception)
        assert str(error) == "Invalid configuration"

    def test_model_not_available_error_inheritance(self):
        """Test ModelNotAvailableError inheritance."""
        error = ModelNotAvailableError("Model not available")
        assert isinstance(error, ModelClientError)
        assert isinstance(error, Exception)
        assert str(error) == "Model not available"

    def test_exception_raising(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(ModelConnectionError):
            raise ModelConnectionError("Test connection error")

        with pytest.raises(ModelRequestError):
            raise ModelRequestError("Test request error")

        with pytest.raises(ModelTimeoutError):
            raise ModelTimeoutError("Test timeout error")

        with pytest.raises(ModelConfigurationError):
            raise ModelConfigurationError("Test configuration error")

        with pytest.raises(ModelNotAvailableError):
            raise ModelNotAvailableError("Test not available error")

    def test_exception_chaining(self):
        """Test exception chaining."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            with pytest.raises(ModelConnectionError) as exc_info:
                raise ModelConnectionError("Wrapped error") from e

            assert exc_info.value.__cause__ is e
