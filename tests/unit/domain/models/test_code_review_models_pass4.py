"""Tests for MultiPassReport with Pass 4 (log analysis) and haiku.

Following TDD principles: tests written before implementation.
"""

import pytest
from datetime import datetime

from src.domain.models.code_review_models import MultiPassReport


class TestMultiPassReportPass4:
    """Test MultiPassReport with Pass 4 log analysis."""

    def test_report_with_pass_4_logs_in_markdown(self) -> None:
        """Test report includes Pass 4 section in markdown."""
        report = MultiPassReport(
            session_id="test-123",
            repo_name="test_repo",
            pass_4_logs={
                "status": "completed",
                "total_log_entries": 100,
                "log_groups_analyzed": 3,
                "results": [
                    {
                        "component": "checker",
                        "classification": "critical",
                        "description": "Redis connection failed",
                        "root_cause": "Container not started",
                        "recommendations": ["Start Redis"],
                        "confidence": 0.95,
                    }
                ],
            },
        )
        markdown = report.to_markdown()
        assert "## Pass 4: Runtime Analysis (Logs)" in markdown
        assert "CHECKER" in markdown or "checker" in markdown.lower()
        assert "Redis connection failed" in markdown

    def test_report_without_pass_4_logs(self) -> None:
        """Test report without Pass 4 still works."""
        report = MultiPassReport(
            session_id="test-123",
            repo_name="test_repo",
            pass_4_logs=None,
        )
        markdown = report.to_markdown()
        assert "## Pass 4: Runtime Analysis (Logs)" not in markdown

    def test_report_with_haiku(self) -> None:
        """Test report includes haiku at the end."""
        report = MultiPassReport(
            session_id="test-123",
            repo_name="test_repo",
            haiku="Code flows onward,\nIssues found, lessons learned—\nImprovement awaits.",
        )
        markdown = report.to_markdown()
        assert "*A code review haiku:*" in markdown
        assert "Code flows onward" in markdown
        assert "Issues found, lessons learned—" in markdown
        assert "Improvement awaits." in markdown

    def test_report_without_haiku(self) -> None:
        """Test report without haiku still works."""
        report = MultiPassReport(
            session_id="test-123",
            repo_name="test_repo",
            haiku=None,
        )
        markdown = report.to_markdown()
        assert "*A code review haiku:*" not in markdown

    def test_pass_4_logs_in_dict(self) -> None:
        """Test pass_4_logs included in to_dict()."""
        pass_4_data = {
            "status": "completed",
            "total_log_entries": 100,
            "log_groups_analyzed": 3,
            "results": [],
        }
        report = MultiPassReport(
            session_id="test-123",
            repo_name="test_repo",
            pass_4_logs=pass_4_data,
        )
        data = report.to_dict()
        assert "pass_4_logs" in data
        assert data["pass_4_logs"] == pass_4_data

    def test_haiku_in_dict(self) -> None:
        """Test haiku included in to_dict()."""
        haiku_text = "Code flows onward,\nIssues found, lessons learned—\nImprovement awaits."
        report = MultiPassReport(
            session_id="test-123",
            repo_name="test_repo",
            haiku=haiku_text,
        )
        data = report.to_dict()
        assert "haiku" in data
        assert data["haiku"] == haiku_text

    def test_pass_4_formatting_with_results(self) -> None:
        """Test Pass 4 section formatting with multiple results."""
        report = MultiPassReport(
            session_id="test-123",
            repo_name="test_repo",
            pass_4_logs={
                "status": "completed",
                "total_log_entries": 200,
                "log_groups_analyzed": 2,
                "results": [
                    {
                        "component": "checker",
                        "classification": "critical",
                        "description": "Issue 1",
                        "root_cause": "Cause 1",
                        "recommendations": ["Fix 1"],
                        "confidence": 0.9,
                    },
                    {
                        "component": "airflow",
                        "classification": "major",
                        "description": "Issue 2",
                        "root_cause": "Cause 2",
                        "recommendations": ["Fix 2"],
                        "confidence": 0.8,
                    },
                ],
            },
        )
        markdown = report.to_markdown()
        assert "**Total Log Entries**: 200" in markdown
        assert "**Issue Groups Found**: 2" in markdown
        assert "[CRITICAL]" in markdown
        assert "[MAJOR]" in markdown

    def test_pass_4_skipped_status(self) -> None:
        """Test Pass 4 with skipped status."""
        report = MultiPassReport(
            session_id="test-123",
            repo_name="test_repo",
            pass_4_logs={"status": "skipped", "reason": "No logs provided"},
        )
        markdown = report.to_markdown()
        assert "## Pass 4: Runtime Analysis (Logs)" not in markdown
