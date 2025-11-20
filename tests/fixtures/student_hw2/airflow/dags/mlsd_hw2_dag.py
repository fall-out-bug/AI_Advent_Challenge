from __future__ import annotations

import json
import os
import pathlib
import zipfile
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Env
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

DATA_DIR = pathlib.Path("/opt/airflow/data/movielens")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_and_unzip():
    import zipfile

    import requests

    zip_path = DATA_DIR / "ml-latest.zip"

    url = "https://files.grouplens.org/datasets/movielens/ml-latest.zip"
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(DATA_DIR)


def upload_to_minio():
    import os

    from minio import Minio

    client = Minio(
        endpoint=MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_ENDPOINT.startswith("https://"),
    )
    for bucket in ["movielens", "features"]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

    # Ищем каталог, где реально лежат CSV
    candidates = [
        DATA_DIR / "ml-latest",  # правильный путь после исправления
        DATA_DIR / "ml-latest" / "ml-latest",  # случай двойной вложенности (на всякий)
        DATA_DIR,  # запасной вариант
    ]
    src_dir = next(
        (
            p
            for p in candidates
            if (p / "ratings.csv").exists() and (p / "movies.csv").exists()
        ),
        None,
    )
    if src_dir is None:
        raise FileNotFoundError(f"Не нашёл csv в {candidates}")

    prefix = "latest/"
    for name in ["ratings.csv", "movies.csv", "links.csv", "tags.csv"]:
        fpath = src_dir / name
        if fpath.exists():
            client.fput_object("movielens", prefix + name, str(fpath))
        else:
            print(f"[warn] нет файла: {fpath}")


default_args = {
    "owner": "mlsd",
    "depends_on_past": False,
    "start_date": datetime(2025, 10, 1),
}

with DAG(
    dag_id="mlsd_hw2",
    default_args=default_args,
    schedule=None,
    catchup=False,
    description="HW2: Download → MinIO → Spark FE → Redis",
) as dag:
    get_dataset = PythonOperator(
        task_id="get_dataset",
        python_callable=download_and_unzip,
    )

    put_dataset = PythonOperator(
        task_id="put_dataset",
        python_callable=upload_to_minio,
    )

    spark_common = (
        "export SPARK_HOME=/opt/spark && "
        "/opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "--conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 "
        "--conf spark.hadoop.fs.s3a.access.key=${MINIO_ROOT_USER} "
        "--conf spark.hadoop.fs.s3a.secret.key=${MINIO_ROOT_PASSWORD} "
        "--conf spark.hadoop.fs.s3a.path.style.access=true "
        "--conf spark.hadoop.fs.s3a.connection.ssl.enabled=false "
        # --- Python на driver/executor ---
        "--conf spark.pyspark.python=/usr/bin/python3 "
        "--conf spark.pyspark.driver.python=/usr/bin/python3 "
        "--conf spark.executorEnv.PYSPARK_PYTHON=/usr/bin/python3 "
        # --- Ресурсы ---
        "--conf spark.executor.cores=2 "
        "--conf spark.executor.memory=6g "
        "--conf spark.driver.memory=3g "
        # --- Шардинг/адаптив ---
        "--conf spark.default.parallelism=200 "
        "--conf spark.sql.shuffle.partitions=200 "
        "--conf spark.sql.adaptive.enabled=true "
        "--conf spark.sql.adaptive.coalescePartitions.enabled=true "
        "--conf spark.sql.adaptive.shuffle.targetPostShuffleInputSize=134217728 "
        # --- Стабильность сети/исполнителей ---
        "--conf spark.speculation=false "
        "--conf spark.executor.heartbeatInterval=30s "
        "--conf spark.network.timeout=600s "
        # --- S3A загрузка (ускоряет запись) ---
        "--conf spark.hadoop.fs.s3a.fast.upload=true "
    )

    spark_common_fe = [
        "--master",
        "spark://spark-master:7077",
        "--deploy-mode",
        "client",
        # одинаковый Python в драйвере и на executors
        "--conf",
        "spark.pyspark.python=/usr/bin/python3",
        "--conf",
        "spark.pyspark.driver.python=/usr/bin/python3",
        "--conf",
        "spark.executorEnv.PYSPARK_PYTHON=/usr/bin/python3",
        # ресурсы (подгони под свою машину; если воркеру тесно — уменьши)
        "--executor-memory",
        "6g",
        "--driver-memory",
        "2g",
        "--conf",
        "spark.executor.memoryOverhead=1024m",
        # шафл/IO
        "--conf",
        "spark.serializer=org.apache.spark.serializer.KryoSerializer",
        "--conf",
        "spark.sql.adaptive.enabled=true",
        "--conf",
        "spark.sql.shuffle.partitions=400",
        "--conf",
        "spark.sql.files.maxPartitionBytes=134217728",
        # S3A/MinIO
        "--conf",
        "spark.hadoop.fs.s3a.endpoint=http://minio:9000",
        "--conf",
        "spark.hadoop.fs.s3a.path.style.access=true",
        "--conf",
        "spark.hadoop.fs.s3a.connection.ssl.enabled=false",
        "--conf",
        "spark.hadoop.fs.s3a.access.key=${MINIO_ROOT_USER}",
        "--conf",
        "spark.hadoop.fs.s3a.secret.key=${MINIO_ROOT_PASSWORD}",
    ]

    features_engineering = BashOperator(
        task_id="features_engineering",
        bash_command=" ".join(
            ["/opt/spark/bin/spark-submit"]
            + spark_common_fe
            + ["/opt/airflow/spark-jobs/features_engineering.py"]
        ),
        env={
            "MINIO_ROOT_USER": MINIO_ACCESS_KEY,
            "MINIO_ROOT_PASSWORD": MINIO_SECRET_KEY,
            # "FE_OUT_PARTITIONS": "256",            # ← важно для больших данных
            # "SPARK_SHUFFLE_PARTITIONS": "1024",    # ← синхронно с конфигом
        },
    )

    load_features = BashOperator(
        task_id="load_features",
        bash_command=spark_common + "/opt/airflow/spark-jobs/load_to_redis.py ",
        env={
            "MINIO_ROOT_USER": MINIO_ACCESS_KEY,
            "MINIO_ROOT_PASSWORD": MINIO_SECRET_KEY,
            "FE_OUT_PARTITIONS": "256",
            "SPARK_SHUFFLE_PARTITIONS": "1024",
        },
    )

    get_dataset >> put_dataset >> features_engineering >> load_features
