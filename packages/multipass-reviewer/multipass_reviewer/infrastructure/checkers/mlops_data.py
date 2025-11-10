"""Heuristic checkers for MLOps and Data Engineering pipelines."""

from __future__ import annotations

from typing import Dict

from multipass_reviewer.infrastructure.checkers.base import BaseChecker


class MLOpsChecker(BaseChecker):
    """Identify common MLOps pipeline gaps (e.g., missing tracking)."""

    name = "mlops"
    default_severity = "major"

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        issues: list[dict[str, object]] = []
        files_scanned = 0

        for path, content in codebase.items():
            lower = content.lower()
            if "mlflow" not in lower and "modelregistry" not in lower:
                continue

            files_scanned += 1

            if "mlflow.log_param" in lower and "mlflow.set_tracking_uri(" not in lower:
                issues.append(
                    {
                        "file": path,
                        "rule": "missing_tracking_uri",
                        "message": (
                            "MLflow usage detected without configuring tracking URI"
                        ),
                    }
                )

            if "mlflow.register_model" not in lower and "register_model" not in lower:
                issues.append(
                    {
                        "file": path,
                        "rule": "missing_model_registry",
                        "message": (
                            "Model training code should register artifacts "
                            "in a model registry"
                        ),
                    }
                )

        metadata: dict[str, object] = {"files_scanned": files_scanned}
        return issues, metadata


class DataPipelineChecker(BaseChecker):
    """Lint data pipelines for schema evolution and quality markers."""

    name = "data_pipeline"
    default_severity = "major"

    def _collect(
        self, codebase: Dict[str, str]
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        issues: list[dict[str, object]] = []
        files_scanned = 0

        for path, content in codebase.items():
            lower = content.lower()
            if (
                "read_csv" not in lower
                and "read.parquet" not in lower
                and "withcolumn" not in lower
            ):
                continue

            files_scanned += 1

            if "mergeschema" in lower or "option('mergeschema'" in lower:
                issues.append(
                    {
                        "file": path,
                        "rule": "runtime_schema_evolution",
                        "message": (
                            "mergeSchema usage may indicate runtime schema drift; "
                            "prefer explicit schema management"
                        ),
                    }
                )

            if (
                "dropna" not in lower
                and "fillna" not in lower
                and "drop_duplicates" not in lower
            ):
                issues.append(
                    {
                        "file": path,
                        "rule": "no_data_quality_steps",
                        "message": (
                            "Pipeline lacks explicit data quality steps "
                            "(dropna/fillna/drop_duplicates)"
                        ),
                    }
                )

        metadata: dict[str, object] = {"files_scanned": files_scanned}
        return issues, metadata
