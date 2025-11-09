"""Health check API routes.

Following the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
- Flat is better than nested
"""

from typing import Dict

from fastapi import APIRouter

from src.infrastructure.config.settings import Settings
from src.infrastructure.health.health_checker import HealthStatus
from src.infrastructure.health.model_health import ModelHealthChecker
from src.infrastructure.health.storage_health import StorageHealthChecker


def create_health_router(settings: Settings) -> APIRouter:
    """Create health check router.

    Args:
        settings: Application settings

    Returns:
        Configured health router
    """
    router = APIRouter(prefix="/health", tags=["health"])

    checkers = {
        "storage": StorageHealthChecker(settings),
        "models": ModelHealthChecker(),
    }

    @router.get("/")
    async def health_check() -> Dict:
        """Simple health check endpoint.

        Returns:
            Health status (always 200 OK)
        """
        return {"status": "ok"}

    @router.get("/ready")
    async def readiness_check() -> Dict:
        """Detailed readiness check.

        Returns:
            Detailed health status
        """
        results = {}
        overall_healthy = True

        for name, checker in checkers.items():
            result = await checker.check()
            results[name] = {
                "status": result.status.value,
                "message": result.message,
                "response_time_ms": result.response_time_ms,
                "details": result.details,
            }

            if result.status != HealthStatus.HEALTHY:
                overall_healthy = False

        return {
            "overall": "ready" if overall_healthy else "degraded",
            "checks": results,
        }

    @router.get("/models")
    async def model_health() -> Dict:
        """Model-specific health check.

        Returns:
            Model availability status
        """
        checker = checkers["models"]
        result = await checker.check()

        return {
            "status": result.status.value,
            "message": result.message,
            "response_time_ms": result.response_time_ms,
            "details": result.details,
        }

    @router.get("/storage")
    async def storage_health() -> Dict:
        """Storage-specific health check.

        Returns:
            Storage availability status
        """
        checker = checkers["storage"]
        result = await checker.check()

        return {
            "status": result.status.value,
            "message": result.message,
            "response_time_ms": result.response_time_ms,
            "details": result.details,
        }

    return router
