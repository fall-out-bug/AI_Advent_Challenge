"""
Retry utilities for network operations.

This module provides retry functionality with exponential backoff
and circuit breaker patterns for resilient network operations.
"""

import asyncio
import time
import random
from typing import Any, Callable, Optional, List, Type, Union
from dataclasses import dataclass
from enum import Enum

from core.interfaces.protocols import RetryProtocol, CircuitBreakerProtocol


class RetryStrategy(Enum):
    """Retry strategy types."""
    
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    RANDOM = "random"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    backoff_multiplier: float = 2.0
    retryable_exceptions: List[Type[Exception]] = None
    
    def __post_init__(self):
        """Initialize default retryable exceptions."""
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [
                ConnectionError,
                TimeoutError,
                OSError,
            ]


class RetryHandler:
    """Retry handler implementation."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry handler."""
        self.config = config or RetryConfig()
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    raise e
                
                if attempt < self.config.max_attempts - 1:
                    delay = self.get_delay(attempt)
                    await asyncio.sleep(delay)
        
        raise last_exception
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Check if should retry on exception."""
        if attempt >= self.config.max_attempts - 1:
            return False
        
        # Check if exception is retryable
        for retryable_exc in self.config.retryable_exceptions:
            if isinstance(exception, retryable_exc):
                return True
        
        return False
    
    def get_delay(self, attempt: int) -> float:
        """Get delay for retry attempt."""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(0, self.config.base_delay * (attempt + 1))
        else:
            delay = self.config.base_delay
        
        # Apply jitter
        if self.config.jitter:
            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor
        
        # Cap at max delay
        return min(delay, self.config.max_delay)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3
    timeout_exceptions: List[Type[Exception]] = None
    
    def __post_init__(self):
        """Initialize default timeout exceptions."""
        if self.timeout_exceptions is None:
            self.timeout_exceptions = [
                TimeoutError,
                ConnectionError,
            ]


class CircuitBreaker:
    """Circuit breaker implementation."""
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker."""
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == CircuitBreakerState.OPEN
    
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open."""
        return self.state == CircuitBreakerState.HALF_OPEN
    
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed."""
        return self.state == CircuitBreakerState.CLOSED
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self.last_success_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.last_failure_time = time.time()
        self.failure_count += 1
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class ResilientClient:
    """Client with retry and circuit breaker capabilities."""
    
    def __init__(self, 
                 retry_config: Optional[RetryConfig] = None,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        """Initialize resilient client."""
        self.retry_handler = RetryHandler(retry_config)
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry and circuit breaker."""
        async def _execute_with_circuit_breaker():
            return await self.circuit_breaker.call(func, *args, **kwargs)
        
        return await self.retry_handler.execute_with_retry(_execute_with_circuit_breaker)
    
    def get_circuit_breaker_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.circuit_breaker.state
    
    def get_failure_count(self) -> int:
        """Get current failure count."""
        return self.circuit_breaker.failure_count
    
    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to closed state."""
        self.circuit_breaker.state = CircuitBreakerState.CLOSED
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.success_count = 0
    
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed."""
        return self.circuit_breaker.is_closed()
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.circuit_breaker.is_open()
    
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open."""
        return self.circuit_breaker.is_half_open()


class RetryDecorator:
    """Decorator for adding retry functionality."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry decorator."""
        self.config = config or RetryConfig()
        self.retry_handler = RetryHandler(self.config)
    
    def __call__(self, func: Callable) -> Callable:
        """Apply retry decorator to function."""
        async def wrapper(*args, **kwargs):
            return await self.retry_handler.execute_with_retry(func, *args, **kwargs)
        
        return wrapper


class CircuitBreakerDecorator:
    """Decorator for adding circuit breaker functionality."""
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker decorator."""
        self.config = config or CircuitBreakerConfig()
        self.circuit_breaker = CircuitBreaker(self.config)
    
    def __call__(self, func: Callable) -> Callable:
        """Apply circuit breaker decorator to function."""
        async def wrapper(*args, **kwargs):
            return await self.circuit_breaker.call(func, *args, **kwargs)
        
        return wrapper


# Convenience functions
def retry(config: Optional[RetryConfig] = None):
    """Retry decorator."""
    return RetryDecorator(config)


def circuit_breaker(config: Optional[CircuitBreakerConfig] = None):
    """Circuit breaker decorator."""
    return CircuitBreakerDecorator(config)


def create_resilient_client(retry_config: Optional[RetryConfig] = None,
                          circuit_breaker_config: Optional[CircuitBreakerConfig] = None) -> ResilientClient:
    """Create resilient client with retry and circuit breaker."""
    return ResilientClient(retry_config, circuit_breaker_config)
