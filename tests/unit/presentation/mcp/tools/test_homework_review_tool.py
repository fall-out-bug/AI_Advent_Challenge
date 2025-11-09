"""Unit tests for homework review MCP tool helpers."""

from __future__ import annotations

import pytest

from src.presentation.mcp.tools.homework_review_tool import detect_assignment_type

pytestmark = pytest.mark.xfail(
    reason=(
        "Homework review MCP tool deprecated in Stage 02_01; replacement arrives"
        " after EP01 refactor."
    ),
    strict=False,
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

