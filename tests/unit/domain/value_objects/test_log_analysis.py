"""Tests for log analysis value objects.

Following TDD principles: tests written before implementation.
"""

import pytest
from datetime import datetime

from src.domain.value_objects.log_analysis import (
    LogEntry,
    LogGroup,
    LogAnalysisResult,
)


class TestLogEntry:
    """Test LogEntry value object."""

    def test_create_valid_entry(self) -> None:
        """Test creating valid log entry."""
        entry = LogEntry(
            timestamp="2025-11-03 00:29:35",
            level="ERROR",
            component="checker",
            message="Connection failed",
            raw_line="2025-11-03 00:29:35 | ERROR | checker | Connection failed",
        )
        assert entry.timestamp == "2025-11-03 00:29:35"
        assert entry.level == "ERROR"
        assert entry.component == "checker"
        assert entry.message == "Connection failed"

    def test_create_with_optional_fields(self) -> None:
        """Test creating entry with optional fields."""
        entry = LogEntry(
            timestamp="2025-11-03 00:29:35",
            level="WARNING",
            component="airflow",
            message="Warning message",
            traceback="Traceback (most recent call last):\n  File...",
            file_path="dags/test.py",
            line_number=42,
            raw_line="raw line",
        )
        assert entry.traceback is not None
        assert entry.file_path == "dags/test.py"
        assert entry.line_number == 42

    def test_validation_component_required(self) -> None:
        """Test validation fails if component is empty."""
        with pytest.raises(ValueError, match="component required"):
            LogEntry(
                timestamp="2025-11-03 00:29:35",
                level="ERROR",
                component="",
                message="Test",
            )

    def test_validation_invalid_level(self) -> None:
        """Test validation fails for invalid level."""
        with pytest.raises(ValueError, match="Invalid level"):
            LogEntry(
                timestamp="2025-11-03 00:29:35",
                level="INVALID",
                component="test",
                message="Test",
            )

    def test_valid_levels(self) -> None:
        """Test all valid levels are accepted."""
        valid_levels = ["ERROR", "WARNING", "INFO", "DEBUG"]
        for level in valid_levels:
            entry = LogEntry(
                timestamp="2025-11-03 00:29:35",
                level=level,
                component="test",
                message="Test",
            )
            assert entry.level == level


class TestLogGroup:
    """Test LogGroup value object."""

    def test_create_valid_group(self) -> None:
        """Test creating valid log group."""
        entries = [
            LogEntry(
                timestamp="2025-11-03 00:29:35",
                level="ERROR",
                component="checker",
                message="Error 1",
            ),
            LogEntry(
                timestamp="2025-11-03 00:30:00",
                level="ERROR",
                component="checker",
                message="Error 2",
            ),
        ]
        group = LogGroup(
            component="checker",
            severity="error",
            count=2,
            entries=entries,
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:30:00",
            error_pattern="Error {N}",
        )
        assert group.component == "checker"
        assert group.count == 2
        assert len(group.entries) == 2

    def test_sample_content_truncates(self) -> None:
        """Test sample_content truncates to max_lines."""
        entries = [
            LogEntry(
                timestamp=f"2025-11-03 00:29:{i:02d}",
                level="ERROR",
                component="test",
                message=f"Error {i}",
            )
            for i in range(30)
        ]
        group = LogGroup(
            component="test",
            severity="error",
            count=30,
            entries=entries,
            first_occurrence="2025-11-03 00:29:00",
            last_occurrence="2025-11-03 00:29:29",
            error_pattern="Error {N}",
        )
        sample = group.sample_content(max_lines=10)
        lines = sample.split("\n")
        assert len(lines) <= 10

    def test_sample_content_includes_traceback(self) -> None:
        """Test sample_content includes traceback if present."""
        entry = LogEntry(
            timestamp="2025-11-03 00:29:35",
            level="ERROR",
            component="test",
            message="Error",
            traceback="Traceback line 1\nTraceback line 2",
        )
        group = LogGroup(
            component="test",
            severity="error",
            count=1,
            entries=[entry],
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:29:35",
            error_pattern="Error",
        )
        sample = group.sample_content()
        assert "Traceback" in sample

    def test_sample_content_truncates_traceback(self) -> None:
        """Test sample_content truncates long traceback."""
        long_traceback = "A" * 1000
        entry = LogEntry(
            timestamp="2025-11-03 00:29:35",
            level="ERROR",
            component="test",
            message="Error",
            traceback=long_traceback,
        )
        group = LogGroup(
            component="test",
            severity="error",
            count=1,
            entries=[entry],
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:29:35",
            error_pattern="Error",
        )
        sample = group.sample_content()
        assert len(sample) < len(long_traceback) + 100


class TestLogAnalysisResult:
    """Test LogAnalysisResult value object."""

    def test_create_valid_result(self) -> None:
        """Test creating valid analysis result."""
        log_group = LogGroup(
            component="checker",
            severity="error",
            count=5,
            entries=[],
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:30:00",
            error_pattern="Connection failed",
        )
        result = LogAnalysisResult(
            log_group=log_group,
            classification="critical",
            description="Redis connection failed",
            root_cause="Container not started",
            recommendations=["Start Redis", "Check network"],
            confidence=0.95,
        )
        assert result.classification == "critical"
        assert result.confidence == 0.95
        assert len(result.recommendations) == 2

    def test_validation_confidence_range(self) -> None:
        """Test validation fails for confidence outside 0.0-1.0."""
        log_group = LogGroup(
            component="test",
            severity="error",
            count=1,
            entries=[],
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:29:35",
            error_pattern="Error",
        )
        with pytest.raises(ValueError, match="confidence must be 0.0-1.0"):
            LogAnalysisResult(
                log_group=log_group,
                classification="minor",
                description="Test",
                root_cause="Test",
                recommendations=[],
                confidence=1.5,
            )

    def test_validation_invalid_classification(self) -> None:
        """Test validation fails for invalid classification."""
        log_group = LogGroup(
            component="test",
            severity="error",
            count=1,
            entries=[],
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:29:35",
            error_pattern="Error",
        )
        with pytest.raises(ValueError, match="Invalid classification"):
            LogAnalysisResult(
                log_group=log_group,
                classification="invalid",
                description="Test",
                root_cause="Test",
                recommendations=[],
                confidence=0.5,
            )

    def test_valid_classifications(self) -> None:
        """Test all valid classifications are accepted."""
        valid_classifications = ["critical", "major", "minor", "warning"]
        log_group = LogGroup(
            component="test",
            severity="error",
            count=1,
            entries=[],
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:29:35",
            error_pattern="Error",
        )
        for classification in valid_classifications:
            result = LogAnalysisResult(
                log_group=log_group,
                classification=classification,
                description="Test",
                root_cause="Test",
                recommendations=[],
                confidence=0.5,
            )
            assert result.classification == classification

    def test_to_markdown_format(self) -> None:
        """Test to_markdown produces correct format."""
        log_group = LogGroup(
            component="checker",
            severity="error",
            count=3,
            entries=[],
            first_occurrence="2025-11-03 00:29:35",
            last_occurrence="2025-11-03 00:30:00",
            error_pattern="Connection failed",
        )
        result = LogAnalysisResult(
            log_group=log_group,
            classification="critical",
            description="Redis connection failed",
            root_cause="Container not started",
            recommendations=["Start Redis", "Check network"],
            confidence=0.95,
        )
        markdown = result.to_markdown()
        assert "[CRITICAL]" in markdown
        assert "checker" in markdown
        assert "**Count:** 3" in markdown
        assert "Redis connection failed" in markdown
        assert "Container not started" in markdown
        assert "1. Start Redis" in markdown
        assert "2. Check network" in markdown
        assert "95%" in markdown
