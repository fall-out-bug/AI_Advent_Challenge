"""
Input validation models using Pydantic.

Following Python Zen: "Explicit is better than implicit"
and "Errors should never pass silently".
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class ModelRequest(BaseModel):
    """
    Validated model request.

    This model ensures all inputs to model APIs are properly validated
    and sanitized before processing.
    """

    model_name: str = Field(
        ..., min_length=1, max_length=50, description="Name of the model to use"
    )
    prompt: str = Field(
        ..., min_length=1, max_length=50000, description="Input prompt for the model"
    )
    max_tokens: Optional[int] = Field(
        default=10000, ge=1, le=100000, description="Maximum tokens to generate"
    )
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )

    @validator("model_name")
    def validate_model_name(cls, v):
        """Validate model name format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Model name must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v.lower()

    @validator("prompt")
    def validate_prompt(cls, v):
        """Validate and sanitize prompt."""
        # Remove excessive whitespace
        v = re.sub(r"\s+", " ", v.strip())

        # Check for potentially harmful content
        dangerous_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"data:text/html",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Prompt contains potentially harmful content")

        return v

    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        """Validate max_tokens value."""
        if v is not None and v <= 0:
            raise ValueError("max_tokens must be positive")
        return v

    @validator("temperature")
    def validate_temperature(cls, v):
        """Validate temperature value."""
        if v is not None and (v < 0.0 or v > 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


class ModelResponse(BaseModel):
    """
    Validated model response.

    This model ensures all responses from model APIs are properly validated
    before being returned to clients.
    """

    response: str = Field(
        ..., min_length=0, max_length=100000, description="Generated response text"
    )
    input_tokens: int = Field(..., ge=0, description="Number of input tokens")
    response_tokens: int = Field(..., ge=0, description="Number of response tokens")
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    model_name: str = Field(
        ..., min_length=1, max_length=50, description="Name of the model used"
    )
    response_time: float = Field(..., ge=0.0, description="Response time in seconds")

    @validator("response")
    def validate_response(cls, v):
        """Validate response content."""
        # Remove excessive whitespace
        v = re.sub(r"\s+", " ", v.strip())
        return v

    @validator("total_tokens")
    def validate_total_tokens(cls, v, values):
        """Validate total_tokens matches sum of input and response tokens."""
        if "input_tokens" in values and "response_tokens" in values:
            expected_total = values["input_tokens"] + values["response_tokens"]
            if v != expected_total:
                raise ValueError(
                    f"total_tokens ({v}) must equal input_tokens + response_tokens ({expected_total})"
                )
        return v


class ChatMessage(BaseModel):
    """
    Validated chat message.

    This model ensures chat messages are properly formatted and safe.
    """

    role: str = Field(
        ..., regex=r"^(system|user|assistant)$", description="Message role"
    )
    content: str = Field(
        ..., min_length=1, max_length=50000, description="Message content"
    )

    @validator("content")
    def validate_content(cls, v):
        """Validate and sanitize message content."""
        # Remove excessive whitespace
        v = re.sub(r"\s+", " ", v.strip())

        # Check for potentially harmful content
        dangerous_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"data:text/html",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Message contains potentially harmful content")

        return v


class ChatRequest(BaseModel):
    """
    Validated chat request with multiple messages.

    This model ensures chat requests with conversation history are properly validated.
    """

    messages: List[ChatMessage] = Field(
        ..., min_items=1, max_items=100, description="List of chat messages"
    )
    max_tokens: Optional[int] = Field(
        default=10000, ge=1, le=100000, description="Maximum tokens to generate"
    )
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )

    @validator("messages")
    def validate_messages(cls, v):
        """Validate message sequence."""
        if not v:
            raise ValueError("At least one message is required")

        # Check that first message is system or user
        if v[0].role not in ["system", "user"]:
            raise ValueError("First message must be from system or user")

        # Check for reasonable conversation length
        total_length = sum(len(msg.content) for msg in v)
        if total_length > 100000:  # 100KB limit
            raise ValueError("Total conversation length exceeds limit")

        return v


class ModelAvailabilityRequest(BaseModel):
    """
    Validated model availability check request.
    """

    model_name: str = Field(
        ..., min_length=1, max_length=50, description="Name of the model to check"
    )

    @validator("model_name")
    def validate_model_name(cls, v):
        """Validate model name format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Model name must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v.lower()


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_model_request(data: Dict[str, Any]) -> ModelRequest:
    """
    Validate model request data.

    Args:
        data: Raw request data

    Returns:
        ModelRequest: Validated request

    Raises:
        ValidationError: If validation fails
    """
    try:
        return ModelRequest(**data)
    except Exception as e:
        raise ValidationError(f"Validation failed: {str(e)}")


def validate_chat_request(data: Dict[str, Any]) -> ChatRequest:
    """
    Validate chat request data.

    Args:
        data: Raw request data

    Returns:
        ChatRequest: Validated request

    Raises:
        ValidationError: If validation fails
    """
    try:
        return ChatRequest(**data)
    except Exception as e:
        raise ValidationError(f"Validation failed: {str(e)}")


def validate_model_response(data: Dict[str, Any]) -> ModelResponse:
    """
    Validate model response data.

    Args:
        data: Raw response data

    Returns:
        ModelResponse: Validated response

    Raises:
        ValidationError: If validation fails
    """
    try:
        return ModelResponse(**data)
    except Exception as e:
        raise ValidationError(f"Validation failed: {str(e)}")


def sanitize_input(text: str) -> str:
    """
    Sanitize user input text.

    Args:
        text: Raw input text

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text.strip())

    # Remove potentially harmful characters
    text = re.sub(r'[<>"\']', "", text)

    return text
