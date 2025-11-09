"""Unit tests for MLOps and Data Engineering checkers."""

from __future__ import annotations

import pytest
from multipass_reviewer.infrastructure.checkers.mlops_data import (
    DataPipelineChecker,
    MLOpsChecker,
)


@pytest.mark.asyncio
async def test_mlops_checker_requires_model_registry() -> None:
    checker = MLOpsChecker()
    code = {
        "pipelines/train.py": (
            "import mlflow\n"
            "def train():\n"
            "    mlflow.log_param('lr', 0.01)\n"
            "    # missing mlflow.set_tracking_uri\n"
        )
    }

    result = await checker.run(code)

    assert any(issue["rule"] == "missing_tracking_uri" for issue in result.issues)


@pytest.mark.asyncio
async def test_data_pipeline_checker_warns_on_schema_changes() -> None:
    checker = DataPipelineChecker()
    code = {
        "jobs/etl.py": (
            "import pyspark.sql.functions as F\n"
            "new_df = df.withColumn('new_col', F.lit(1))\n"
            "new_df.write.option('mergeSchema', 'true').parquet('/tmp/out')\n"
        )
    }

    result = await checker.run(code)

    assert any(issue["rule"] == "runtime_schema_evolution" for issue in result.issues)
