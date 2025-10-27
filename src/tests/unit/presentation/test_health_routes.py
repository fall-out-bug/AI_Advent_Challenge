"""Tests for health API routes.

Following TDD principles:
- Test API endpoints
- Mock dependencies
- Clear assertions
"""

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.config.settings import Settings
from src.infrastructure.health.health_checker import HealthStatus
from src.presentation.api.health_routes import create_health_router


class TestHealthRoutes:
    """Test health routes."""

    @pytest.fixture
    def settings(self, tmp_path):
        """Create test settings."""
        return Settings(storage_path=tmp_path)

    @pytest.fixture
    def client(self, settings):
        """Create test client."""
        from fastapi import FastAPI

        app = FastAPI()
        router = create_health_router(settings)
        app.include_router(router)
        return TestClient(app)

    def test_health_check(self, client):
        """Test simple health check."""
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_readiness_check(self, client):
        """Test readiness check."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "checks" in data

    def test_model_health(self, client):
        """Test model health check."""
        response = client.get("/health/models")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data

    def test_storage_health(self, client):
        """Test storage health check."""
        response = client.get("/health/storage")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data
