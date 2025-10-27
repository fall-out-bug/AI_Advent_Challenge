"""Storage health checker.

Following the Zen of Python:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import time
from pathlib import Path

from src.infrastructure.config.settings import Settings
from src.infrastructure.health.health_checker import (
    HealthChecker,
    HealthResult,
    HealthStatus,
)


class StorageHealthChecker(HealthChecker):
    """Check storage availability."""

    def __init__(self, settings: Settings):
        """Initialize checker.

        Args:
            settings: Application settings
        """
        super().__init__(name="storage_availability")
        self.settings = settings

    async def check(self) -> HealthResult:
        """Check storage availability.

        Returns:
            Health check result
        """
        start_time = time.time()

        try:
            storage_path = self.settings.storage_path
            agent_storage = self.settings.get_agent_storage_path()
            experiment_storage = self.settings.get_experiment_storage_path()

            checks = {
                "base_path": self._check_path(storage_path),
                "agent_storage": self._check_path(agent_storage.parent),
                "experiment_storage": self._check_path(experiment_storage.parent),
                "can_write": self._check_writable(storage_path),
            }

            all_ok = all(checks.values())

            if all_ok:
                status = HealthStatus.HEALTHY
                message = "Storage accessible and writable"
            else:
                status = HealthStatus.DEGRADED
                message = "Storage issues detected"

            response_time = (time.time() - start_time) * 1000

            details = {
                "checks": checks,
                "paths": {
                    "storage": str(storage_path),
                    "agent": str(agent_storage),
                    "experiment": str(experiment_storage),
                },
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
                message=f"Storage check failed: {str(e)}",
                response_time_ms=response_time,
            )

    def _check_path(self, path: Path) -> bool:
        """Check if path exists or can be created.

        Args:
            path: Path to check

        Returns:
            True if path is valid
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path.exists()
        except Exception:
            return False

    def _check_writable(self, path: Path) -> bool:
        """Check if path is writable.

        Args:
            path: Path to check

        Returns:
            True if writable
        """
        try:
            test_file = path / ".health_check_test"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False
