"""Domain exceptions package."""

from src.domain.exceptions.intent_exceptions import (
    ClarificationGenerationError,
    FallbackParseError,
    IntentParseError,
    IntentValidationError,
    LLMParseError,
)
from src.domain.exceptions.pdf_exceptions import (
    PDFCacheError,
    PDFGenerationError,
    PDFRenderError,
    PDFTemplateError,
)

__all__ = [
    # Intent exceptions
    "IntentParseError",
    "LLMParseError",
    "FallbackParseError",
    "IntentValidationError",
    "ClarificationGenerationError",
    # PDF exceptions
    "PDFGenerationError",
    "PDFTemplateError",
    "PDFRenderError",
    "PDFCacheError",
]

