"""
Abstract base classes for model clients.

Following Python Zen: "Explicit is better than implicit"
and "Simple is better than complex".
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import TracebackType
from typing import Optional, Type, TypeVar


@dataclass
class ModelResponse:
    """
    Standard model response structure.

    This dataclass represents a standardized response
    from any model, regardless of type.
    """

    response: str
    response_tokens: int
    input_tokens: int
    total_tokens: int
    model_name: str
    response_time: float


T_BaseClient = TypeVar("T_BaseClient", bound="BaseModelClient")


class BaseModelClient(ABC):
    """Abstract base class for model clients."""

    def __init__(
        self,
        timeout: float = 120.0,
        max_retries: int = 3,
        retry_base_delay: float = 0.5,
    ):
        """Initialize base model client."""
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay

    @abstractmethod
    async def make_request(
        self,
        model_name: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ModelResponse:
        """Make request to model."""
        pass

    @abstractmethod
    async def check_availability(self, model_name: str) -> bool:
        """Check if model is available."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close client resources."""
        pass

    def __enter__(self: T_BaseClient) -> T_BaseClient:
        """Context manager entry."""
        return self

    async def __aenter__(self: T_BaseClient) -> T_BaseClient:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Async context manager exit."""
        await self.close()
