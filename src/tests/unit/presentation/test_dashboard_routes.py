"""Tests for dashboard API routes."""

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.monitoring.metrics import get_metrics
from src.presentation.api.dashboard_routes import create_dashboard_router


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    from fastapi import FastAPI

    app = FastAPI()
    dashboard_router = create_dashboard_router()
    app.include_router(dashboard_router)

    return app


@pytest.fixture
def client(app) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_metrics():
    """Create sample metrics data."""
    metrics = get_metrics()

    # Record some sample data
    for i in range(20):
        metrics.record_request(
            success=i < 18,
            response_time_ms=float(i * 10),
            tokens_used=i * 50,
            operation=f"operation_{i % 5}",
        )

    return metrics


class TestDashboardRoutes:
    """Test dashboard API routes."""

    def test_dashboard_endpoint(self, client: TestClient) -> None:
        """Test dashboard HTML endpoint."""
        response = client.get("/dashboard/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"

        # Check that HTML contains dashboard elements
        content = response.text
        assert "AI Challenge Metrics Dashboard" in content
        assert "dashboard" in content.lower()

    def test_dashboard_data_endpoint(self, client: TestClient, sample_metrics) -> None:
        """Test dashboard data endpoint."""
        response = client.get("/dashboard/data")

        assert response.status_code == 200

        data = response.json()

        assert "metrics" in data
        assert "recent_operations" in data

        metrics_data = data["metrics"]

        assert "request_count" in metrics_data
        assert metrics_data["request_count"] > 0

        assert "success_rate" in metrics_data
        assert "total_tokens_used" in metrics_data

    def test_dashboard_data_includes_percentiles(
        self, client: TestClient, sample_metrics
    ) -> None:
        """Test that dashboard data includes percentiles."""
        response = client.get("/dashboard/data")
        data = response.json()

        metrics_data = data["metrics"]

        assert "response_time_percentiles" in metrics_data

        percentiles = metrics_data["response_time_percentiles"]

        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles

    def test_dashboard_data_includes_recent_operations(
        self, client: TestClient, sample_metrics
    ) -> None:
        """Test that dashboard data includes recent operations."""
        response = client.get("/dashboard/data")
        data = response.json()

        assert "recent_operations" in data
        assert isinstance(data["recent_operations"], list)

    def test_dashboard_data_recent_operations_structure(
        self, client: TestClient, sample_metrics
    ) -> None:
        """Test structure of recent operations data."""
        response = client.get("/dashboard/data")
        data = response.json()

        recent_ops = data["recent_operations"]

        if recent_ops:
            op = recent_ops[0]

            assert "timestamp" in op
            assert "operation" in op
            assert "response_time_ms" in op
            assert "success" in op

    def test_dashboard_data_empty_metrics(self, client: TestClient) -> None:
        """Test dashboard data with empty metrics."""
        # Reset metrics
        get_metrics().reset()

        response = client.get("/dashboard/data")

        assert response.status_code == 200

        data = response.json()

        assert data["metrics"]["request_count"] == 0
        assert len(data["recent_operations"]) == 0
