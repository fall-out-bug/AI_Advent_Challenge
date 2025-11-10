"""Domain exceptions for intent parsing.

Following the Zen of Python:
- Errors should never pass silently
- Explicit is better than implicit
"""


class IntentParseError(Exception):
    """Base exception for intent parsing errors.

    Args:
        message: Error message
        original_error: Original exception if this is a wrapped error
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize intent parse error.

        Args:
            message: Error message
            original_error: Original exception if this is a wrapped error
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class LLMParseError(IntentParseError):
    """Error during LLM-based intent parsing.

    Raised when LLM parsing fails or returns invalid response.
    """


class FallbackParseError(IntentParseError):
    """Error during fallback deterministic parsing.

    Raised when fallback parser encounters unexpected input.
    """


class IntentValidationError(IntentParseError):
    """Error during intent validation.

    Raised when parsed intent fails validation checks.
    """


class ClarificationGenerationError(IntentParseError):
    """Error during clarification question generation.

    Raised when clarification questions cannot be generated.
    """
