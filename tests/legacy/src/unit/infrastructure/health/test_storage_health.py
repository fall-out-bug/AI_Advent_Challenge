"""Tests for storage health checker.

Following TDD principles and Zen of Python:
- Simple and clear tests
- Comprehensive coverage
- Explicit assertions
"""

import pytest

from src.infrastructure.config.settings import Settings
from src.infrastructure.health.health_checker import HealthStatus
from src.infrastructure.health.storage_health import StorageHealthChecker


class TestStorageHealthChecker:
    """Test storage health checker."""

    @pytest.fixture
    def settings(self, tmp_path):
        """Create test settings."""
        return Settings(storage_path=tmp_path)

    @pytest.fixture
    def checker(self, settings):
        """Create storage checker."""
        return StorageHealthChecker(settings)

    @pytest.mark.asyncio
    async def test_check_healthy(self, checker):
        """Test healthy storage check."""
        result = await checker.check()

        assert result.status == HealthStatus.HEALTHY
        assert "accessible" in result.message.lower()
        assert result.response_time_ms > 0

    @pytest.mark.asyncio
    async def test_check_includes_details(self, checker):
        """Test that check includes details."""
        result = await checker.check()

        assert result.details is not None
        assert "checks" in result.details
        assert "paths" in result.details

    @pytest.mark.asyncio
    async def test_check_path_exists(self, checker, tmp_path):
        """Test path existence check."""
        test_path = tmp_path / "test_dir"
        is_valid = checker._check_path(test_path)

        assert is_valid
        assert test_path.exists()

    @pytest.mark.asyncio
    async def test_check_writable(self, checker, tmp_path):
        """Test writable check."""
        is_writable = checker._check_writable(tmp_path)

        assert is_writable
