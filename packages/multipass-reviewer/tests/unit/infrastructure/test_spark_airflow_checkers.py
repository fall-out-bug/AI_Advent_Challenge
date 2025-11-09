"""Unit tests for Spark and Airflow modular checkers."""

from __future__ import annotations

import pytest
from multipass_reviewer.infrastructure.checkers.spark_airflow import (
    AirflowChecker,
    SparkChecker,
)


@pytest.mark.asyncio
async def test_spark_checker_flags_large_shuffle() -> None:
    checker = SparkChecker()
    code = {
        "jobs/spark_job.py": (
            "from pyspark.sql import SparkSession\n"
            "spark = SparkSession.builder.appName('demo').getOrCreate()\n"
            "df = spark.read.parquet('s3://bucket')\n"
            "joined = df.join(df, on='id')\n"
            "joined.write.mode('overwrite').parquet('s3://out')\n"
        )
    }

    result = await checker.run(code)

    assert result.issues, "Expected Spark checker to surface heuristics"
    assert result.issues[0]["rule"] == "potential_large_shuffle"


@pytest.mark.asyncio
async def test_airflow_checker_detects_missing_default_args() -> None:
    checker = AirflowChecker()
    code = {
        "dags/sample_dag.py": (
            "from airflow import DAG\n"
            "from airflow.operators.python_operator import PythonOperator\n"
            "dag = DAG('example', schedule_interval='@daily')\n"
            "PythonOperator(task_id='t1', python_callable=lambda: None, dag=dag)\n"
        )
    }

    result = await checker.run(code)

    assert any(issue["rule"] == "missing_default_args" for issue in result.issues)
