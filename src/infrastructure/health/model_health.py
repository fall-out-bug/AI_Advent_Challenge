"""Model availability health checker.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Errors should never pass silently
"""

import time
from typing import Dict

import httpx
from yaml import safe_load

from src.infrastructure.health.health_checker import (
    HealthChecker,
    HealthResult,
    HealthStatus,
)


class ModelHealthChecker(HealthChecker):
    """Check model endpoints availability."""

    def __init__(self):
        """Initialize checker."""
        super().__init__(name="model_availability")
        self._timeout_seconds = 5.0

    async def check(self) -> HealthResult:
        """Check model endpoints.

        Returns:
            Health check result
        """
        start_time = time.time()

        try:
            model_configs = self._load_model_configs()
            results = []

            for model_name, endpoint in model_configs.items():
                is_available = await self._check_endpoint(endpoint)
                results.append((model_name, is_available))

            # Determine overall status
            all_healthy = all(available for _, available in results)
            any_healthy = any(available for _, available in results)

            if all_healthy:
                status = HealthStatus.HEALTHY
                message = "All models available"
            elif any_healthy:
                status = HealthStatus.DEGRADED
                message = "Some models unavailable"
            else:
                status = HealthStatus.UNHEALTHY
                message = "All models unavailable"

            response_time = (time.time() - start_time) * 1000

            details = {
                "models": {
                    name: "available" if avail else "unavailable"
                    for name, avail in results
                }
            }

            return HealthResult(
                status=status,
                message=message,
                details=details,
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time_ms=response_time,
            )

    async def _check_endpoint(self, url: str) -> bool:
        """Check if endpoint is reachable.

        Args:
            url: Endpoint URL

        Returns:
            True if reachable
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(url)
                return response.status_code < 500
        except Exception:
            return False

    def _load_model_configs(self) -> Dict[str, str]:
        """Load model configurations.

        Returns:
            Dictionary of model names to endpoints
        """
        from pathlib import Path

        config_path = Path("config/models.yaml")
        if not config_path.exists():
            return {}

        with config_path.open() as f:
            config = safe_load(f)
            models = config.get("models", {})
            return {name: model.get("base_url", "") for name, model in models.items()}
