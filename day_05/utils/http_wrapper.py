"""
HTTP client wrapper for unified error handling.

Following Python Zen: "Simple is better than complex"
and "Don't repeat yourself".
"""

import httpx
from typing import Dict, Any, Optional
from functools import wraps


class HTTPClientWrapper:
    """Unified HTTP client with standardized error handling."""
    
    def __init__(self, timeout: float = 30.0):
        """Initialize HTTP client wrapper."""
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
    
    async def post(
        self, 
        url: str, 
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make POST request with unified error handling."""
        try:
            response = await self.client.post(url, json=json, headers=headers)
            response.raise_for_status()
            return response
        except httpx.ConnectError as e:
            raise HTTPConnectionError(f"Failed to connect to {url}: {e}")
        except httpx.TimeoutException as e:
            raise HTTPTimeoutError(f"Request to {url} timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPRequestError(f"HTTP error for {url}: {e}")
        except Exception as e:
            raise HTTPRequestError(f"Unexpected error with {url}: {e}")
    
    async def get(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make GET request with unified error handling."""
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response
        except httpx.ConnectError as e:
            raise HTTPConnectionError(f"Failed to connect to {url}: {e}")
        except httpx.TimeoutException as e:
            raise HTTPTimeoutError(f"Request to {url} timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPRequestError(f"HTTP error for {url}: {e}")
        except Exception as e:
            raise HTTPRequestError(f"Unexpected error with {url}: {e}")


class HTTPError(Exception):
    """Base HTTP error."""
    pass


class HTTPConnectionError(HTTPError):
    """HTTP connection error."""
    pass


class HTTPTimeoutError(HTTPError):
    """HTTP timeout error."""
    pass


class HTTPRequestError(HTTPError):
    """HTTP request error."""
    pass


def http_error_handler(func):
    """Decorator for HTTP error handling."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPError:
            raise
        except Exception as e:
            raise HTTPRequestError(f"Unexpected error in {func.__name__}: {e}")
    return wrapper
