"""Domain exceptions for PDF generation.

Following the Zen of Python:
- Errors should never pass silently
- Explicit is better than implicit
"""


class PDFGenerationError(Exception):
    """Base exception for PDF generation errors.

    Args:
        message: Error message
        original_error: Original exception if this is a wrapped error
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize PDF generation error.

        Args:
            message: Error message
            original_error: Original exception if this is a wrapped error
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class PDFTemplateError(PDFGenerationError):
    """Error during PDF template rendering.

    Raised when template rendering fails.
    """


class PDFRenderError(PDFGenerationError):
    """Error during PDF rendering.

    Raised when PDF rendering fails (e.g., WeasyPrint errors).
    """


class PDFCacheError(PDFGenerationError):
    """Error during PDF caching operations.

    Raised when caching operations fail.
    """
