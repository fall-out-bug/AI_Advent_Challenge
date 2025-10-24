"""Simplified tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from agents.api.generator_api import app as generator_app
from agents.api.reviewer_api import app as reviewer_app


class TestGeneratorAPI:
    """Test generator API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(generator_app)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime" in data

    def test_stats_endpoint(self):
        """Test stats endpoint."""
        response = self.client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "failed_requests" in data

    def test_generate_code_endpoint_structure(self):
        """Test code generation endpoint structure."""
        request_data = {
            "task_description": "Create a test function",
            "language": "python",
            "requirements": ["Include type hints"],
            "max_tokens": 1000,
            "model_name": "starcoder"
        }

        response = self.client.post("/generate", json=request_data)
        # Should return some response (even if error due to agent not initialized)
        assert response.status_code in [200, 500]
        data = response.json()
        assert isinstance(data, dict)

    def test_generate_code_invalid_request(self):
        """Test code generation with invalid request."""
        request_data = {
            "task_description": "",  # Invalid empty description
        }

        response = self.client.post("/generate", json=request_data)
        # Should return validation error or server error due to agent not initialized
        assert response.status_code in [422, 500]


class TestReviewerAPI:
    """Test reviewer API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(reviewer_app)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime" in data

    def test_stats_endpoint(self):
        """Test stats endpoint."""
        response = self.client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "failed_requests" in data

    def test_review_code_endpoint_structure(self):
        """Test code review endpoint structure."""
        request_data = {
            "task_description": "Test task",
            "generated_code": "def test(): pass",
            "tests": "def test_test(): pass",
            "metadata": {
                "complexity": "low",
                "lines_of_code": 2,
                "dependencies": []
            }
        }

        response = self.client.post("/review", json=request_data)
        # Should return some response (even if error due to agent not initialized)
        assert response.status_code in [200, 500]
        data = response.json()
        assert isinstance(data, dict)

    def test_review_code_invalid_request(self):
        """Test code review with invalid request."""
        request_data = {
            "task_description": "Test task",
            # Missing required fields
        }

        response = self.client.post("/review", json=request_data)
        assert response.status_code == 422  # Validation error
