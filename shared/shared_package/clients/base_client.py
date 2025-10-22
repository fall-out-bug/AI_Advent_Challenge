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
    """
    Abstract base class for model clients.
    
    Following Python Zen: "Explicit is better than implicit"
    and "Simple is better than complex".
    
    This class defines the interface that all model clients
    must implement, ensuring consistency across different
    model types and implementations.
    """
    
    def __init__(self, timeout: float = 120.0):
        """
        Initialize base model client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    @abstractmethod
    async def make_request(
        self, 
        model_name: str, 
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> ModelResponse:
        """
        Make request to model.
        
        Args:
            model_name: Name of the model
            prompt: Input prompt
            max_tokens: Maximum tokens to generate (optional)
            temperature: Generation temperature (optional)
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            ModelConnectionError: If connection fails
            ModelRequestError: If request fails
            ModelTimeoutError: If request times out
        """
        pass
    
    @abstractmethod
    async def check_availability(self, model_name: str) -> bool:
        """
        Check if model is available.
        
        Args:
            model_name: Name of the model
            
        Returns:
            bool: True if model is available
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close client resources.
        
        This method should clean up any resources
        used by the client (e.g., HTTP connections).
        """
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
