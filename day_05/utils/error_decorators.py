"""
Error handling decorators for HTTP requests.

Following Python Zen: "Simple is better than complex"
and "Don't repeat yourself".
"""

import functools
import asyncio
from typing import Callable, Any, Optional
from utils.http_wrapper import HTTPError, HTTPConnectionError, HTTPTimeoutError, HTTPRequestError


def retry_on_error(
    max_retries: int = 3, 
    delay: float = 1.0, 
    backoff_factor: float = 2.0
):
    """Decorator for retrying HTTP requests on error."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except HTTPError as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff_factor ** attempt)
                        await asyncio.sleep(wait_time)
                        continue
                    break
                except Exception as e:
                    # Don't retry on non-HTTP errors
                    raise HTTPRequestError(f"Unexpected error in {func.__name__}: {e}")
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def handle_http_errors(func: Callable) -> Callable:
    """Decorator for unified HTTP error handling."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except HTTPConnectionError as e:
            raise HTTPConnectionError(f"Connection failed in {func.__name__}: {e}")
        except HTTPTimeoutError as e:
            raise HTTPTimeoutError(f"Timeout in {func.__name__}: {e}")
        except HTTPRequestError as e:
            raise HTTPRequestError(f"Request failed in {func.__name__}: {e}")
        except Exception as e:
            raise HTTPRequestError(f"Unexpected error in {func.__name__}: {e}")
    
    return wrapper


def log_http_requests(func: Callable) -> Callable:
    """Decorator for logging HTTP requests."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # Simple logging - in production, use proper logging
        print(f"🌐 Making HTTP request: {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            print(f"✅ HTTP request successful: {func.__name__}")
            return result
        except HTTPError as e:
            print(f"❌ HTTP request failed: {func.__name__} - {e}")
            raise
        except Exception as e:
            print(f"💥 Unexpected error: {func.__name__} - {e}")
            raise
    
    return wrapper


def timeout_protection(timeout_seconds: float = 30.0):
    """Decorator for adding timeout protection to HTTP requests."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs), 
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                raise HTTPTimeoutError(f"Request timed out after {timeout_seconds}s in {func.__name__}")
        
        return wrapper
    return decorator


def circuit_breaker(
    failure_threshold: int = 5, 
    recovery_timeout: float = 60.0
):
    """Simple circuit breaker decorator for HTTP requests."""
    def decorator(func: Callable) -> Callable:
        failure_count = 0
        last_failure_time = 0.0
        circuit_open = False
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            nonlocal failure_count, last_failure_time, circuit_open
            
            current_time = asyncio.get_event_loop().time()
            
            # Check if circuit should be closed
            if circuit_open and (current_time - last_failure_time) > recovery_timeout:
                circuit_open = False
                failure_count = 0
            
            # If circuit is open, reject request
            if circuit_open:
                raise HTTPRequestError(f"Circuit breaker open for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                # Reset failure count on success
                failure_count = 0
                return result
            except HTTPError as e:
                failure_count += 1
                last_failure_time = current_time
                
                if failure_count >= failure_threshold:
                    circuit_open = True
                
                raise e
        
        return wrapper
    return decorator
