"""Tests for model health checker.

Following TDD principles:
- Tests first, implementation after
- Mock external dependencies
- Clear test scenarios
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.health.health_checker import HealthStatus
from src.infrastructure.health.model_health import ModelHealthChecker


class TestModelHealthChecker:
    """Test model health checker."""

    @pytest.fixture
    def checker(self):
        """Create model checker."""
        return ModelHealthChecker()

    @pytest.mark.asyncio
    async def test_check_endpoint_healthy(self, checker):
        """Test healthy endpoint check."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            is_available = await checker._check_endpoint("http://test.com")

            assert is_available

    @pytest.mark.asyncio
    async def test_check_endpoint_unhealthy(self, checker):
        """Test unhealthy endpoint check."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection error")
            )

            is_available = await checker._check_endpoint("http://test.com")

            assert not is_available

    @pytest.mark.asyncio
    async def test_load_model_configs_empty_when_no_config(self, checker):
        """Test loading config when file doesn't exist."""
        configs = checker._load_model_configs()

        assert isinstance(configs, dict)
