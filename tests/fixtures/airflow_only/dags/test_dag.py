"""Test Airflow DAG."""

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator


def hello_world():
    """Print hello world."""
    print("Hello World!")


with DAG(
    dag_id="test_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    task1 = PythonOperator(
        task_id="hello_task",
        python_callable=hello_world,
    )
