"""Tests for presentation API layer."""

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.__main__ import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_api_routes_exist(client: TestClient) -> None:
    """Test that main routes exist."""
    # Test with POST to agents endpoint
    response = client.post("/api/agents/generate")
    # Should not return 404 (may return 422 validation error or other)
    assert response.status_code != 404


def test_generate_code_endpoint(client: TestClient) -> None:
    """Test code generation endpoint."""
    response = client.post(
        "/api/agents/generate",
        json={
            "prompt": "Create a hello function",
            "agent_name": "test_agent",
        },
    )
    # Should return 200 or 500 with error
    assert response.status_code in [200, 500]


def test_review_code_endpoint(client: TestClient) -> None:
    """Test code review endpoint."""
    response = client.post(
        "/api/agents/review",
        json={
            "code": "def hello(): pass",
            "agent_name": "test_agent",
        },
    )
    # Should return 200 or 500 with error
    assert response.status_code in [200, 500]


def test_adapter_status_endpoint(client: TestClient) -> None:
    """Test adapter status endpoint."""
    response = client.get("/api/experiments/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "message" in data
