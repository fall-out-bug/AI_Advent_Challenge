"""
Abstract base classes for model clients.

Following Python Zen: "Explicit is better than implicit"
and "Simple is better than complex".
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..exceptions.model_errors import ModelClientError


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
    async def make_request(self, model_name: str, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> ModelResponse:
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
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
