"""
Standardized exceptions for model operations.

Following Python Zen: "Explicit is better than implicit".
"""


class ModelClientError(Exception):
    """
    Base exception for model client errors.
    
    This is the base class for all model-related exceptions.
    """
    pass


class ModelConnectionError(ModelClientError):
    """
    Raised when model connection fails.
    
    This exception is raised when there are network issues
    or the model service is unreachable.
    """
    pass


class ModelRequestError(ModelClientError):
    """
    Raised when model request fails.
    
    This exception is raised when the request is malformed
    or the model returns an error response.
    """
    pass


class ModelTimeoutError(ModelClientError):
    """
    Raised when model request times out.
    
    This exception is raised when the request takes longer
    than the configured timeout.
    """
    pass


class ModelConfigurationError(ModelClientError):
    """
    Raised when model configuration is invalid.
    
    This exception is raised when the model configuration
    is missing required fields or contains invalid values.
    """
    pass


class ModelNotAvailableError(ModelClientError):
    """
    Raised when model is not available.
    
    This exception is raised when trying to use a model
    that is not currently available or running.
    """
    pass
