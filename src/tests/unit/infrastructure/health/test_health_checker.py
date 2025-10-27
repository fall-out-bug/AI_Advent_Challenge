"""Tests for health checker base class.

Following TDD principles:
- Tests written first
- Comprehensive coverage
- Clear assertions
"""

import pytest

from src.infrastructure.health.health_checker import (
    HealthChecker,
    HealthResult,
    HealthStatus,
)


class TestHealthChecker:
    """Test health checker base functionality."""

    def test_health_status_enum(self):
        """Test health status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_result_creation(self):
        """Test health result creation."""
        result = HealthResult(
            status=HealthStatus.HEALTHY, message="Test message", response_time_ms=10.5
        )

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Test message"
        assert result.response_time_ms == 10.5
        assert result.details is None

    def test_health_result_with_details(self):
        """Test health result with details."""
        details = {"component": "test", "available": True}
        result = HealthResult(
            status=HealthStatus.HEALTHY, message="Test", details=details
        )

        assert result.details == details

    def test_checker_name(self):
        """Test checker name getter."""

        class TestChecker(HealthChecker):
            async def check(self) -> HealthResult:
                return HealthResult(status=HealthStatus.HEALTHY, message="Test")

        checker = TestChecker("test_name")
        assert checker.get_name() == "test_name"
