"""Integration tests for multipart review endpoint.

Following TDD principles.
"""

import pytest
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.application.use_cases.enqueue_review_task_use_case import (
    EnqueueReviewTaskUseCase,
)
from src.application.use_cases.get_review_status_use_case import (
    GetReviewStatusUseCase,
)
from src.infrastructure.config.settings import Settings
from src.presentation.api.review_routes import create_review_router


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


class TestMultipartReviewEndpoint:
    """Test multipart review endpoint."""

    def test_create_review_with_multipart_files(
        self, test_client: TestClient
    ) -> None:
        """Test creating review with multipart file upload."""
        # Create test ZIP files
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as new_zip:
            with zipfile.ZipFile(new_zip.name, "w") as zf:
                zf.writestr("main.py", "print('hello')")
            new_zip_path = new_zip.name

        try:
            with open(new_zip_path, "rb") as f:
                files = {
                    "new_zip": ("new.zip", f, "application/zip"),
                }
                data = {
                    "student_id": "2001",
                    "assignment_id": "hw2",
                    "new_commit": "abc123",
                }
                response = test_client.post(
                    "/api/v1/reviews",
                    files=files,
                    data=data,
                )
            assert response.status_code == 201
            result = response.json()
            assert "task_id" in result
            assert result["status"] == "queued"
        finally:
            Path(new_zip_path).unlink()

    def test_create_review_with_logs(
        self, test_client: TestClient
    ) -> None:
        """Test creating review with logs archive."""
        # Create test ZIP files
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as new_zip:
            with zipfile.ZipFile(new_zip.name, "w") as zf:
                zf.writestr("main.py", "print('hello')")
            new_zip_path = new_zip.name

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as logs_zip:
            with zipfile.ZipFile(logs_zip.name, "w") as zf:
                zf.writestr("logs/checker.log", "2025-11-03 | ERROR | test | Error")
            logs_zip_path = logs_zip.name

        try:
            with open(new_zip_path, "rb") as nf, open(logs_zip_path, "rb") as lf:
                files = {
                    "new_zip": ("new.zip", nf, "application/zip"),
                    "logs_zip": ("logs.zip", lf, "application/zip"),
                }
                data = {
                    "student_id": "2001",
                    "assignment_id": "hw2",
                    "new_commit": "abc123",
                }
                response = test_client.post(
                    "/api/v1/reviews",
                    files=files,
                    data=data,
                )
            assert response.status_code == 201
            result = response.json()
            assert "task_id" in result
        finally:
            Path(new_zip_path).unlink()
            Path(logs_zip_path).unlink()

    def test_create_review_missing_new_zip(
        self, test_client: TestClient
    ) -> None:
        """Test creating review without required new_zip."""
        data = {
            "student_id": "2001",
            "assignment_id": "hw2",
        }
        response = test_client.post(
            "/api/v1/reviews",
            data=data,
        )
        assert response.status_code == 422  # Validation error

    def test_create_review_empty_new_commit(self, test_client: TestClient) -> None:
        """Test that empty new_commit returns 400."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as new_zip:
            with zipfile.ZipFile(new_zip.name, "w") as zf:
                zf.writestr("main.py", "print('hello')")
            new_zip_path = new_zip.name

        try:
            with open(new_zip_path, "rb") as f:
                files = {
                    "new_zip": ("new.zip", f, "application/zip"),
                }
                data = {
                    "student_id": "2001",
                    "assignment_id": "hw2",
                    "new_commit": "   ",
                }
                response = test_client.post(
                    "/api/v1/reviews",
                    files=files,
                    data=data,
                )
            assert response.status_code == 400
            assert response.json()["detail"] == "new_commit cannot be empty"
        finally:
            Path(new_zip_path).unlink()

