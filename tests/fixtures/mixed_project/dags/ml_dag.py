"""ML Pipeline DAG."""

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="ml_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
) as dag:
    train_task = BashOperator(
        task_id="train_model",
        bash_command="python train.py",
    )
