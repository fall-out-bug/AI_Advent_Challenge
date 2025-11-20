"""Tests for EnqueueReviewTaskUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.enqueue_review_task_use_case import (
    EnqueueReviewTaskUseCase,
)
from src.domain.value_objects.long_summarization_task import LongTask
from src.domain.value_objects.task_status import TaskStatus
from src.domain.value_objects.task_type import TaskType


@pytest.mark.asyncio
async def test_enqueue_review_task_creates_task():
    """Test EnqueueReviewTaskUseCase creates task."""
    mock_repo = AsyncMock()
    use_case = EnqueueReviewTaskUseCase(mock_repo)

    task = await use_case.execute(
        student_id="123",
        assignment_id="HW2",
        new_submission_path="/path/to/new.zip",
        previous_submission_path="/path/to/old.zip",
        new_commit="commit123",
    )

    assert isinstance(task, LongTask)
    assert task.task_type == TaskType.CODE_REVIEW
    assert task.user_id == 123  # Converted from student_id
    assert task.metadata["student_id"] == "123"
    assert task.metadata["assignment_id"] == "HW2"
    assert task.metadata["new_submission_path"] == "/path/to/new.zip"
    assert task.metadata["previous_submission_path"] == "/path/to/old.zip"
    assert task.metadata["new_commit"] == "commit123"
    assert task.status == TaskStatus.QUEUED
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_enqueue_review_task_without_previous():
    """Test EnqueueReviewTaskUseCase without previous submission."""
    mock_repo = AsyncMock()
    use_case = EnqueueReviewTaskUseCase(mock_repo)

    task = await use_case.execute(
        student_id="456",
        assignment_id="HW2",
        new_submission_path="/path/to/new.zip",
        new_commit="commit456",
    )

    assert task.metadata.get("previous_submission_path") is None
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_enqueue_review_task_invalid_student_id():
    """Test EnqueueReviewTaskUseCase with invalid student_id."""
    mock_repo = AsyncMock()
    use_case = EnqueueReviewTaskUseCase(mock_repo)

    with pytest.raises(ValueError, match="student_id must be numeric"):
        await use_case.execute(
            student_id="not_a_number",
            assignment_id="HW2",
            new_submission_path="/path/to/new.zip",
            new_commit="commit_invalid",
        )


@pytest.mark.asyncio
async def test_enqueue_review_task_empty_new_commit():
    """Test EnqueueReviewTaskUseCase rejects empty new_commit."""
    mock_repo = AsyncMock()
    use_case = EnqueueReviewTaskUseCase(mock_repo)

    with pytest.raises(ValueError, match="new_commit cannot be empty"):
        await use_case.execute(
            student_id="123",
            assignment_id="HW2",
            new_submission_path="/path/to/new.zip",
            new_commit="   ",
        )
