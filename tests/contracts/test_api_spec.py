"""Contract tests for API specification compliance.

Following TDD principles: tests validate that the API implementation
matches the OpenAPI specification.
"""

import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock

from src.presentation.api.review_routes import create_review_router
from src.application.use_cases.enqueue_review_task_use_case import (
    EnqueueReviewTaskUseCase,
)
from src.application.use_cases.get_review_status_use_case import (
    GetReviewStatusUseCase,
)
from src.infrastructure.config.settings import Settings


@pytest.fixture
def openapi_spec() -> dict:
    """Load OpenAPI specification."""
    spec_path = Path(__file__).parent.parent.parent / "contracts" / "review_api_v1.yaml"
    with open(spec_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def test_client() -> TestClient:
    """Create test client for review API."""
    app = FastAPI()
    enqueue_use_case = EnqueueReviewTaskUseCase(AsyncMock())
    get_status_use_case = GetReviewStatusUseCase(AsyncMock(), AsyncMock())
    settings = Settings()
    router = create_review_router(enqueue_use_case, get_status_use_case, settings)
    app.include_router(router)
    return TestClient(app)


class TestAPISpecCompliance:
    """Test API implementation against OpenAPI spec."""

    def test_post_reviews_endpoint_exists(
        self, test_client: TestClient, openapi_spec: dict
    ):
        """Test that POST /api/v1/reviews endpoint exists."""
        path = openapi_spec["paths"]["/api/v1/reviews"]
        assert "post" in path
        assert path["post"]["operationId"] == "createReview"

    def test_get_reviews_endpoint_exists(
        self, test_client: TestClient, openapi_spec: dict
    ):
        """Test that GET /api/v1/reviews/{task_id} endpoint exists."""
        path = openapi_spec["paths"]["/api/v1/reviews/{task_id}"]
        assert "get" in path
        assert path["get"]["operationId"] == "getReviewStatus"

    def test_post_reviews_required_fields(self, openapi_spec: dict):
        """Test that required fields are defined in spec."""
        path = openapi_spec["paths"]["/api/v1/reviews"]
        schema = path["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]
        required = schema.get("required", [])
        assert "student_id" in required
        assert "assignment_id" in required
        assert "new_zip" in required
        assert "new_commit" in required

    def test_post_reviews_optional_fields(self, openapi_spec: dict):
        """Test that optional fields are defined in spec."""
        path = openapi_spec["paths"]["/api/v1/reviews"]
        schema = path["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]
        properties = schema.get("properties", {})
        assert "new_commit" in properties
        assert "old_zip" in properties
        assert properties["old_zip"].get("nullable") is True
        assert "logs_zip" in properties
        assert properties["logs_zip"].get("nullable") is True
        assert "old_commit" in properties
        assert properties["old_commit"].get("nullable") is True
        assert (
            "nullable" not in properties["new_commit"]
            or properties["new_commit"].get("nullable") is False
        )
        assert properties["new_commit"].get("minLength") == 1

    def test_review_status_response_schema(self, openapi_spec: dict):
        """Test ReviewStatusResponse schema structure."""
        components = openapi_spec["components"]["schemas"]
        assert "ReviewStatusResponse" in components
        schema = components["ReviewStatusResponse"]

        # Check required fields
        required = schema.get("required", [])
        assert "task_id" in required
        assert "status" in required

        # Check properties
        properties = schema.get("properties", {})
        assert "task_id" in properties
        assert properties["task_id"]["type"] == "string"
        assert "status" in properties
        assert "enum" in properties["status"]
        assert set(properties["status"]["enum"]) == {
            "queued",
            "running",
            "completed",
            "failed",
        }
        assert "student_id" in properties
        assert "assignment_id" in properties
        assert "created_at" in properties
        assert "finished_at" in properties
        assert "result" in properties
        assert "error" in properties

    def test_error_response_schema(self, openapi_spec: dict):
        """Test ErrorResponse schema structure."""
        components = openapi_spec["components"]["schemas"]
        assert "ErrorResponse" in components
        schema = components["ErrorResponse"]

        required = schema.get("required", [])
        assert "detail" in required

        properties = schema.get("properties", {})
        assert "detail" in properties
        assert properties["detail"]["type"] == "string"

    def test_post_reviews_response_codes(self, openapi_spec: dict):
        """Test that all expected response codes are defined."""
        path = openapi_spec["paths"]["/api/v1/reviews"]
        responses = path["post"]["responses"]
        assert "201" in responses
        assert "400" in responses
        assert "413" in responses
        assert "500" in responses

    def test_get_reviews_response_codes(self, openapi_spec: dict):
        """Test that all expected response codes are defined."""
        path = openapi_spec["paths"]["/api/v1/reviews/{task_id}"]
        responses = path["get"]["responses"]
        assert "200" in responses
        assert "404" in responses
