"""Health checking infrastructure.

Following the Zen of Python:
- Simple is better than complex
- Errors should never pass silently
- Explicit is better than implicit
"""

from src.infrastructure.health.health_checker import HealthChecker, HealthResult

__all__ = ["HealthChecker", "HealthResult"]
