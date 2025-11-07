"""Tests for SubmissionArchive value object."""

import pytest
from datetime import datetime

from src.domain.value_objects.submission_archive import SubmissionArchive


def test_submission_archive_creation():
    """Test SubmissionArchive creation with valid data."""
    archive = SubmissionArchive(
        submission_id="sub_123",
        archive_path="/path/to/archive.zip",
        extracted_path="/tmp/extracted",
        code_files={"main.py": "def hello(): pass"},
        test_logs="Tests passed: 10/10",
        metadata={"size": 1024, "files_count": 5},
    )
    assert archive.submission_id == "sub_123"
    assert len(archive.code_files) == 1
    assert archive.test_logs == "Tests passed: 10/10"


def test_submission_archive_minimal():
    """Test SubmissionArchive with minimal data."""
    archive = SubmissionArchive(
        submission_id="sub_123",
        archive_path="/path/to/archive.zip",
        extracted_path="/tmp/extracted",
    )
    assert archive.code_files == {}
    assert archive.test_logs is None
    assert archive.metadata == {}


def test_submission_archive_validation_empty_id():
    """Test SubmissionArchive validation fails with empty submission_id."""
    with pytest.raises(ValueError, match="submission_id cannot be empty"):
        SubmissionArchive(
            submission_id="",
            archive_path="/path/to/archive.zip",
            extracted_path="/tmp/extracted",
        )


def test_submission_archive_validation_empty_path():
    """Test SubmissionArchive validation fails with empty archive_path."""
    with pytest.raises(ValueError, match="archive_path cannot be empty"):
        SubmissionArchive(
            submission_id="sub_123",
            archive_path="",
            extracted_path="/tmp/extracted",
        )

