"""Tests for LongTask metadata with log analysis fields.

Following TDD principles.
"""

import pytest
from datetime import datetime

from src.domain.value_objects.long_summarization_task import LongTask
from src.domain.value_objects.task_type import TaskType
from src.domain.value_objects.task_status import TaskStatus


class TestLongTaskMetadata:
    """Test LongTask metadata with log analysis fields."""

    def test_metadata_with_commits_and_logs(self) -> None:
        """Test LongTask with commit hashes and logs path in metadata."""
        task = LongTask(
            task_id="test-123",
            task_type=TaskType.CODE_REVIEW,
            user_id=2001,
            metadata={
                "new_submission_path": "/path/to/new.zip",
                "previous_submission_path": "/path/to/old.zip",
                "assignment_id": "hw2",
                "new_commit": "abc123def456",
                "old_commit": "prev789",
                "logs_zip_path": "/path/to/logs.zip",
            },
        )
        assert task.metadata["new_commit"] == "abc123def456"
        assert task.metadata["old_commit"] == "prev789"
        assert task.metadata["logs_zip_path"] == "/path/to/logs.zip"

    def test_metadata_serialization(self) -> None:
        """Test metadata is preserved in to_dict/from_dict."""
        original = LongTask(
            task_id="test-123",
            task_type=TaskType.CODE_REVIEW,
            user_id=2001,
            metadata={
                "new_commit": "abc123",
                "old_commit": "prev789",
                "logs_zip_path": "/path/to/logs.zip",
            },
        )
        data = original.to_dict()
        restored = LongTask.from_dict(data)
        assert restored.metadata["new_commit"] == "abc123"
        assert restored.metadata["old_commit"] == "prev789"
        assert restored.metadata["logs_zip_path"] == "/path/to/logs.zip"

    def test_metadata_optional_fields(self) -> None:
        """Test that commit and logs fields are optional."""
        task = LongTask(
            task_id="test-123",
            task_type=TaskType.CODE_REVIEW,
            user_id=2001,
            metadata={
                "new_submission_path": "/path/to/new.zip",
            },
        )
        assert "new_commit" not in task.metadata
        assert "old_commit" not in task.metadata
        assert "logs_zip_path" not in task.metadata

