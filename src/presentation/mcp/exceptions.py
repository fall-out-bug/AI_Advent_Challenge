"""Domain-specific exceptions for MCP operations."""
from typing import Any, Optional


class MCPBaseException(Exception):
    """Base exception for all MCP errors."""

    def __init__(
        self, message: str, context: Optional[dict[str, Any]] = None
    ) -> None:
        """Initialize exception.

        Args:
            message: Error message
            context: Additional context information
        """
        super().__init__(message)
        self.context = context or {}


class MCPAdapterError(MCPBaseException):
    """Error in adapter operations."""

    pass


class MCPModelError(MCPBaseException):
    """Error related to model operations."""

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize model error.

        Args:
            message: Error message
            model_name: Name of the model
            context: Additional context
        """
        super().__init__(message, context)
        if model_name:
            self.context["model_name"] = model_name


class MCPAgentError(MCPBaseException):
    """Error in agent operations."""

    def __init__(
        self,
        message: str,
        agent_type: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize agent error.

        Args:
            message: Error message
            agent_type: Type of agent (generator/reviewer)
            context: Additional context
        """
        super().__init__(message, context)
        if agent_type:
            self.context["agent_type"] = agent_type


class MCPOrchestrationError(MCPBaseException):
    """Error in orchestration workflows."""

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize orchestration error.

        Args:
            message: Error message
            stage: Workflow stage that failed
            context: Additional context
        """
        super().__init__(message, context)
        if stage:
            self.context["stage"] = stage


class MCPValidationError(MCPBaseException):
    """Error in input validation."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            context: Additional context
        """
        super().__init__(message, context)
        if field:
            self.context["field"] = field
        if value is not None:
            self.context["value"] = value
