"""Heuristic checkers for Spark and Airflow pipelines."""

from __future__ import annotations

from typing import Dict

from multipass_reviewer.infrastructure.checkers.base import BaseChecker


class SparkChecker(BaseChecker):
    """Detect common Spark anti-patterns that impact performance."""

    name = "spark"
    default_severity = "major"

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        issues: list[dict[str, object]] = []
        files_scanned = 0

        for path, content in codebase.items():
            lower = content.lower()
            if "pyspark" not in lower and "sparksession" not in lower:
                continue

            files_scanned += 1

            if ".join(" in lower and "broadcast(" not in lower:
                issues.append(
                    {
                        "file": path,
                        "rule": "potential_large_shuffle",
                        "message": "Spark join without broadcast hint detected",
                    }
                )

            if "repartition(" in lower and "repartition(1" in lower:
                issues.append(
                    {
                        "file": path,
                        "rule": "single_partition_output",
                        "message": "Writing with repartition(1) may create bottlenecks",
                    }
                )

        metadata: dict[str, object] = {"files_scanned": files_scanned}
        return issues, metadata


class AirflowChecker(BaseChecker):
    """Detect Airflow DAG definition issues."""

    name = "airflow"
    default_severity = "major"

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        issues: list[dict[str, object]] = []
        files_scanned = 0

        for path, content in codebase.items():
            lower = content.lower()
            if "airflow" not in lower or "dag(" not in lower:
                continue

            files_scanned += 1

            if "default_args" not in lower:
                issues.append(
                    {
                        "file": path,
                        "rule": "missing_default_args",
                        "message": (
                            "Airflow DAG should define default_args "
                            "for retries/owner"
                        ),
                    }
                )

            if "schedule_interval" not in lower:
                issues.append(
                    {
                        "file": path,
                        "rule": "missing_schedule_interval",
                        "message": (
                            "Airflow DAG missing schedule_interval declaration"
                        ),
                    }
                )

        metadata: dict[str, object] = {"files_scanned": files_scanned}
        return issues, metadata
