"""Abstract health checker interface.

Following the Zen of Python:
- Explicit is better than implicit
- Simple is better than complex
- Readability counts
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class HealthStatus(Enum):
    """Health status enum."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthResult:
    """Result of a health check.

    Attributes:
        status: Health status
        message: Human-readable message
        details: Optional additional details
        timestamp: When check was performed
    """

    status: HealthStatus
    message: str
    details: Optional[Dict] = None
    response_time_ms: float = 0.0


class HealthChecker(ABC):
    """Abstract health checker interface.

    Following single responsibility principle:
    Each checker validates one component of the system.
    """

    def __init__(self, name: str):
        """Initialize checker.

        Args:
            name: Checker name
        """
        self.name = name

    @abstractmethod
    async def check(self) -> HealthResult:
        """Perform health check.

        Returns:
            Health check result
        """

    def get_name(self) -> str:
        """Get checker name.

        Returns:
            Checker name
        """
        return self.name
