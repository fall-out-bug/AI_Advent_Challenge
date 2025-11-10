"""Tests for use case result types."""

import pytest
from pydantic import ValidationError

from src.application.dtos.butler_use_case_dtos import (
    DigestResult,
    StatsResult,
    TaskCreationResult,
)


class TestTaskCreationResult:
    """Test suite for TaskCreationResult."""

    def test_successful_creation(self):
        """Test successful task creation result."""
        result = TaskCreationResult(created=True, task_id="507f1f77bcf86cd799439011")
        assert result.created is True
        assert result.task_id == "507f1f77bcf86cd799439011"
        assert result.clarification is None
        assert result.error is None

    def test_clarification_result(self):
        """Test clarification needed result."""
        result = TaskCreationResult(
            created=False, clarification="What is the deadline?"
        )
        assert result.created is False
        assert result.clarification == "What is the deadline?"
        assert result.task_id is None
        assert result.error is None

    def test_error_result(self):
        """Test error result."""
        result = TaskCreationResult(created=False, error="Failed to create task")
        assert result.created is False
        assert result.error == "Failed to create task"
        assert result.task_id is None
        assert result.clarification is None


class TestDigestResult:
    """Test suite for DigestResult."""

    def test_successful_digest(self):
        """Test successful digest result."""
        digests = [{"channel": "python", "posts_count": 5, "summary": "Test summary"}]
        result = DigestResult(digests=digests)
        assert len(result.digests) == 1
        assert result.digests[0]["channel"] == "python"
        assert result.error is None

    def test_empty_digests(self):
        """Test empty digests result."""
        result = DigestResult()
        assert result.digests == []
        assert result.error is None

    def test_error_result(self):
        """Test error result."""
        result = DigestResult(error="Failed to fetch digests")
        assert result.error == "Failed to fetch digests"
        assert result.digests == []


class TestStatsResult:
    """Test suite for StatsResult."""

    def test_successful_stats(self):
        """Test successful stats result."""
        stats = {"total_students": 25, "active_students": 20}
        result = StatsResult(stats=stats)
        assert result.stats["total_students"] == 25
        assert result.stats["active_students"] == 20
        assert result.error is None

    def test_empty_stats(self):
        """Test empty stats result."""
        result = StatsResult()
        assert result.stats == {}
        assert result.error is None

    def test_error_result(self):
        """Test error result."""
        result = StatsResult(error="Failed to fetch stats")
        assert result.error == "Failed to fetch stats"
        assert result.stats == {}
