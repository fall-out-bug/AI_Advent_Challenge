"""Token information value objects."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class TokenCount:
    """
    Immutable token count value object.

    Attributes:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        total_tokens: Total number of tokens
    """

    input_tokens: int
    output_tokens: int
    total_tokens: int

    def __post_init__(self) -> None:
        """Validate token counts."""
        if self.input_tokens < 0:
            raise ValueError("Input tokens cannot be negative")
        if self.output_tokens < 0:
            raise ValueError("Output tokens cannot be negative")
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("Total tokens must equal sum of input and output tokens")

    @property
    def ratio(self) -> float:
        """Calculate output to input ratio."""
        if self.input_tokens == 0:
            return 0.0
        return self.output_tokens / self.input_tokens


@dataclass(frozen=True)
class TokenInfo:
    """
    Comprehensive token information value object.

    Attributes:
        token_count: Token count information
        model_name: Name of the model used
        metadata: Optional additional metadata
    """

    token_count: TokenCount
    model_name: str
    metadata: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        """Validate token info."""
        if not self.model_name:
            raise ValueError("Model name cannot be empty")
