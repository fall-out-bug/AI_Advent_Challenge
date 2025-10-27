"""Custom exceptions for the multi-agent system."""


class MultiAgentError(Exception):
    """Base exception for multi-agent system errors."""

    pass


class CodeGenerationError(MultiAgentError):
    """Raised when code generation fails."""

    pass


class CodeReviewError(MultiAgentError):
    """Raised when code review fails."""

    pass


class ValidationError(MultiAgentError):
    """Raised when input validation fails."""

    pass


class StarCoderError(MultiAgentError):
    """Raised when StarCoder service fails."""

    pass


class AgentCommunicationError(MultiAgentError):
    """Raised when agent-to-agent communication fails."""

    pass


class ConfigurationError(MultiAgentError):
    """Raised when configuration is invalid."""

    pass


class RateLimitError(MultiAgentError):
    """Raised when rate limit is exceeded."""

    pass
