"""
Typed exceptions with context for better debugging.

Following Python Zen: "Explicit is better than implicit"
and "Errors should never pass silently".
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import traceback


@dataclass
class ErrorContext:
    """Context information for exceptions."""
    timestamp: datetime
    module: str
    function: str
    line_number: int
    variables: Dict[str, Any]
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class BaseTypedException(Exception):
    """Base class for typed exceptions with context."""
    
    def __init__(
        self, 
        message: str, 
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        """Initialize typed exception."""
        super().__init__(message)
        self.message = message
        self.context = context or self._create_default_context()
        self.cause = cause
        self.traceback = traceback.format_exc()
    
    def _create_default_context(self) -> ErrorContext:
        """Create default context from current frame."""
        import inspect
        frame = inspect.currentframe().f_back.f_back
        
        return ErrorContext(
            timestamp=datetime.now(),
            module=frame.f_globals.get('__name__', 'unknown'),
            function=frame.f_code.co_name,
            line_number=frame.f_lineno,
            variables={}
        )
    
    def add_variable(self, name: str, value: Any) -> 'BaseTypedException':
        """Add variable to context."""
        self.context.variables[name] = value
        return self
    
    def add_request_data(self, data: Dict[str, Any]) -> 'BaseTypedException':
        """Add request data to context."""
        self.context.request_data = data
        return self
    
    def add_response_data(self, data: Dict[str, Any]) -> 'BaseTypedException':
        """Add response data to context."""
        self.context.response_data = data
        return self
    
    def add_user_context(self, user_id: str, session_id: Optional[str] = None) -> 'BaseTypedException':
        """Add user context to exception."""
        self.context.user_id = user_id
        self.context.session_id = session_id
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'context': {
                'timestamp': self.context.timestamp.isoformat(),
                'module': self.context.module,
                'function': self.context.function,
                'line_number': self.context.line_number,
                'variables': self.context.variables,
                'request_data': self.context.request_data,
                'response_data': self.context.response_data,
                'user_id': self.context.user_id,
                'session_id': self.context.session_id
            },
            'cause': str(self.cause) if self.cause else None,
            'traceback': self.traceback
        }
    
    def __str__(self) -> str:
        """String representation with context."""
        return f"{self.__class__.__name__}: {self.message} (at {self.context.module}.{self.context.function}:{self.context.line_number})"


class ModelException(BaseTypedException):
    """Base exception for model-related errors."""
    pass


class ModelConnectionException(ModelException):
    """Exception for model connection errors."""
    
    def __init__(
        self, 
        model_name: str, 
        url: str, 
        error: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Failed to connect to model '{model_name}' at {url}: {error}"
        super().__init__(message, context, cause)
        self.model_name = model_name
        self.url = url
        self.error = error


class ModelRequestException(ModelException):
    """Exception for model request errors."""
    
    def __init__(
        self, 
        model_name: str, 
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        if status_code:
            message = f"Request to model '{model_name}' failed with status {status_code}"
        elif error_message:
            message = f"Request to model '{model_name}' failed: {error_message}"
        else:
            message = f"Request to model '{model_name}' failed"
        
        super().__init__(message, context, cause)
        self.model_name = model_name
        self.status_code = status_code
        self.error_message = error_message


class ModelTimeoutException(ModelException):
    """Exception for model timeout errors."""
    
    def __init__(
        self, 
        model_name: str, 
        timeout_seconds: float,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Request to model '{model_name}' timed out after {timeout_seconds}s"
        super().__init__(message, context, cause)
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds


class ModelConfigurationException(ModelException):
    """Exception for model configuration errors."""
    
    def __init__(
        self, 
        model_name: str, 
        config_error: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Configuration error for model '{model_name}': {config_error}"
        super().__init__(message, context, cause)
        self.model_name = model_name
        self.config_error = config_error


class ValidationException(BaseTypedException):
    """Exception for validation errors."""
    
    def __init__(
        self, 
        field_name: str, 
        value: Any, 
        validation_rule: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Validation failed for field '{field_name}': {validation_rule} (value: {value})"
        super().__init__(message, context, cause)
        self.field_name = field_name
        self.value = value
        self.validation_rule = validation_rule


class BusinessLogicException(BaseTypedException):
    """Exception for business logic errors."""
    
    def __init__(
        self, 
        operation: str, 
        reason: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Business logic error in '{operation}': {reason}"
        super().__init__(message, context, cause)
        self.operation = operation
        self.reason = reason


def create_error_context(
    variables: Optional[Dict[str, Any]] = None,
    request_data: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> ErrorContext:
    """Create error context with current frame information."""
    import inspect
    frame = inspect.currentframe().f_back
    
    return ErrorContext(
        timestamp=datetime.now(),
        module=frame.f_globals.get('__name__', 'unknown'),
        function=frame.f_code.co_name,
        line_number=frame.f_lineno,
        variables=variables or {},
        request_data=request_data,
        response_data=response_data,
        user_id=user_id,
        session_id=session_id
    )
