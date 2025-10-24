"""Tests for API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from agents.api.generator_api import app as generator_app
from agents.api.reviewer_api import app as reviewer_app
from communication.message_schema import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    TaskMetadata,
)
from datetime import datetime


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

    @patch("agents.api.generator_api.CodeGeneratorAgent")
    def test_generate_code_endpoint(self, mock_agent_class):
        """Test code generation endpoint."""
        # Mock agent initialization
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock the agent instance in the module
        with patch("agents.api.generator_api.agent", mock_agent):
            # Mock response
            mock_response = CodeGenerationResponse(
                task_description="Test task",
                generated_code="def test(): pass",
                tests="def test_test(): pass",
                metadata=TaskMetadata(
                    complexity="low",
                    lines_of_code=2,
                    dependencies=[]
                ),
                generation_time=datetime.now(),
                tokens_used=100
            )
            mock_agent.process.return_value = mock_response

            # Test request
            request_data = {
                "task_description": "Create a test function",
                "language": "python",
                "requirements": ["Include type hints"],
                "max_tokens": 1000,
                "model_name": "starcoder"
            }

            response = self.client.post("/generate", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["task_description"] == "Test task"
            assert data["generated_code"] == "def test(): pass"

    def test_generate_code_invalid_request(self):
        """Test code generation with invalid request."""
        request_data = {
            "task_description": "",  # Invalid empty description
        }

        response = self.client.post("/generate", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch("agents.api.generator_api.CodeGeneratorAgent")
    def test_generate_code_agent_error(self, mock_agent_class):
        """Test code generation with agent error."""
        # Mock agent to raise exception
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.process.side_effect = Exception("Agent error")

        request_data = {
            "task_description": "Create a test function",
        }

        response = self.client.post("/generate", json=request_data)
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


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

    @patch("agents.api.reviewer_api.CodeReviewerAgent")
    def test_review_code_endpoint(self, mock_agent_class):
        """Test code review endpoint."""
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        # Mock response
        from communication.message_schema import CodeQualityMetrics
        mock_response = CodeReviewResponse(
            code_quality_score=8.5,
            metrics=CodeQualityMetrics(
                pep8_compliance=True,
                pep8_score=9.0,
                has_docstrings=True,
                has_type_hints=True,
                complexity_score=3.0,
                test_coverage="high"
            ),
            suggestions=["Add more comments"],
            recommendations=["Consider using dataclasses"],
            issues=["Minor formatting issue"],
            review_time=datetime.now(),
            tokens_used=150
        )
        mock_agent.process.return_value = mock_response

        # Test request
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
        assert response.status_code == 200
        data = response.json()
        assert data["code_quality_score"] == 8.5
        assert data["metrics"]["pep8_compliance"] is True

    def test_review_code_invalid_request(self):
        """Test code review with invalid request."""
        request_data = {
            "task_description": "Test task",
            # Missing required fields
        }

        response = self.client.post("/review", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch("agents.api.reviewer_api.CodeReviewerAgent")
    def test_review_code_agent_error(self, mock_agent_class):
        """Test code review with agent error."""
        # Mock agent to raise exception
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.process.side_effect = Exception("Agent error")

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
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
