"""Unit tests for homework review MCP tool helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.domain.models.code_review_models import (
    Finding,
    MultiPassReport,
    PassFindings,
    SeverityLevel,
)
from src.presentation.mcp.tools.homework_review_tool import (
    detect_assignment_type,
    review_homework_archive,
)


class TestDetectAssignmentType:
    """Test suite for detect_assignment_type function."""

    def test_detect_hw1_docker_spark(self) -> None:
        """Detect HW1 when Dockerfile and Spark usage present."""
        codebase = {
            "Dockerfile": "FROM python:3.9",
            "src/main.py": "from pyspark.sql import SparkSession",
        }

        result = detect_assignment_type(codebase)

        assert result == "HW1"

    def test_detect_hw1_missing_components(self) -> None:
        """Return auto when Docker or Spark components are missing."""
        codebase = {"src/main.py": "print('hello world')"}

        result = detect_assignment_type(codebase)

        assert result == "auto"

    def test_detect_hw2_airflow(self) -> None:
        """Detect HW2 when Airflow references present."""
        codebase = {"airflow/dags/sample.py": "from airflow import DAG"}

        result = detect_assignment_type(codebase)

        assert result == "HW2"

    def test_detect_hw3_mlflow(self) -> None:
        """Detect HW3 when MLflow usage present."""
        codebase = {
            "mlflow/tracking.py": "import mlflow",
            "pipeline.py": "mlflow.log_metric('score', 0.9)",
        }

        result = detect_assignment_type(codebase)

        assert result == "HW3"

    def test_priority_hw3_over_hw2(self) -> None:
        """Prefer HW3 classification when MLflow and Airflow coexist."""
        codebase = {
            "mlflow/tracking.py": "import mlflow",
            "airflow/dags/my_dag.py": "from airflow import DAG",
        }

        result = detect_assignment_type(codebase)

        assert result == "HW3"

    def test_case_insensitive_detection(self) -> None:
        """Detection should be case-insensitive for file paths and contents."""
        codebase = {
            "AIRFLOW/dags/my_dag.py": "from airflow import DAG",
            "MLFLOW/track.py": "import mlfLow",
        }

        result = detect_assignment_type(codebase)

        assert result == "HW3"

    def test_unknown_structure_returns_auto(self) -> None:
        """Return auto for repositories without known patterns."""
        codebase = {
            "README.md": "# Project",
            "src/app.py": "print('hello')",
        }

        result = detect_assignment_type(codebase)

        assert result == "auto"


@pytest.mark.asyncio
async def test_review_homework_archive_success(tmp_path, monkeypatch):
    """Happy-path review: report persisted and response serialized."""
    archive_path = tmp_path / "homework.zip"
    archive_path.write_bytes(b"placeholder")

    fake_submission = SimpleNamespace(
        code_files={
            "Dockerfile": "FROM python",
            "src/main.py": "from pyspark.sql import SparkSession",
        },
        metadata={"files_count": 2, "total_size_bytes": 1280},
    )

    def fake_extract(self, archive_path: str, submission_id: str):
        return fake_submission

    monkeypatch.setattr(
        "src.presentation.mcp.tools.homework_review_tool.ZipArchiveService.extract_submission",
        fake_extract,
    )

    fake_report = MultiPassReport(
        session_id="session-123",
        repo_name="homework",
        pass_1=PassFindings(
            pass_name="pass_1",
            findings=[
                Finding(
                    severity=SeverityLevel.MAJOR,
                    title="Issue",
                    description="Needs refactor",
                )
            ],
        ),
    )
    fake_report.pass_2_results = {
        "pass_2_spark": PassFindings(pass_name="pass_2_spark")
    }
    fake_report.detected_components = ["spark"]
    fake_report.total_findings = 1
    fake_report.execution_time_seconds = 4.2

    fake_service = SimpleNamespace(
        review_submission=AsyncMock(return_value=fake_report)
    )
    monkeypatch.setattr(
        "src.presentation.mcp.tools.homework_review_tool.ModularReviewService",
        lambda *_, **__: fake_service,
    )

    markdown_report = "# Detailed Review\n\nSummary line."
    monkeypatch.setattr(
        "src.presentation.mcp.tools.homework_review_tool.generate_detailed_markdown_report",
        AsyncMock(return_value=markdown_report),
    )

    created_clients = []

    class DummyClient:
        def __init__(self) -> None:
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    def client_factory(*_, **__):
        client = DummyClient()
        created_clients.append(client)
        return client

    monkeypatch.setattr(
        "src.presentation.mcp.tools.homework_review_tool.UnifiedModelClient",
        client_factory,
    )

    fake_repo = SimpleNamespace(
        save_review_session=AsyncMock(),
        save_logs=AsyncMock(),
    )
    monkeypatch.setattr(
        "src.presentation.mcp.tools.homework_review_tool.HomeworkReviewRepository",
        lambda *_args, **_kwargs: fake_repo,
    )
    monkeypatch.setattr(
        "src.presentation.mcp.tools.homework_review_tool.get_db",
        AsyncMock(return_value=object()),
    )

    result = await review_homework_archive(str(archive_path))

    assert result["success"] is True
    assert result["assignment_type"] == "HW1"
    assert result["markdown_report"] == markdown_report
    assert result["detected_components"] == ["spark"]
    assert result["pass_2_components"] == ["pass_2_spark"]
    assert created_clients and created_clients[0].closed is True
    fake_service.review_submission.assert_awaited_once()
    fake_repo.save_review_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_review_homework_archive_missing_file(tmp_path):
    """Missing archive should raise FileNotFoundError."""
    missing = tmp_path / "missing.zip"
    with pytest.raises(FileNotFoundError):
        await review_homework_archive(str(missing))
