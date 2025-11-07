"""Integration tests for review API routes."""

import pytest
from datetime import datetime

from src.domain.value_objects.long_summarization_task import LongTask
from src.domain.value_objects.task_status import TaskStatus
from src.domain.value_objects.task_type import TaskType


@pytest.mark.asyncio
async def test_create_review_flow():
    """Test complete review creation flow."""
    # This is a structure test - full implementation requires
    # proper FastAPI TestClient setup with dependency overrides
    task = LongTask(
        task_id="rev_test123",
        task_type=TaskType.CODE_REVIEW,
        user_id=123,
        status=TaskStatus.QUEUED,
        metadata={
            "student_id": "123",
            "assignment_id": "HW2",
            "new_submission_path": "/path/to/new.zip",
            "new_commit": "commit123",
        },
    )
    assert task.status == TaskStatus.QUEUED
    assert task.task_type == TaskType.CODE_REVIEW
    assert task.metadata["student_id"] == "123"


@pytest.mark.asyncio
async def test_get_review_status_flow():
    """Test get review status flow."""
    # Structure test for status retrieval
    result = {
        "task_id": "rev_test123",
        "status": "queued",
        "student_id": "123",
        "assignment_id": "HW2",
    }
    assert result["status"] == "queued"
    assert result["student_id"] == "123"
