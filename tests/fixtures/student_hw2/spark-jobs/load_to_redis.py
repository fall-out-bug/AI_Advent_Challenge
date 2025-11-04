# spark-jobs/load_to_redis.py
import os, json
from pyspark.sql import SparkSession, functions as F

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS   = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

FEATURES_PATH = os.getenv("FEATURES_PATH", "s3a://features/users/")

def build_session():
    # S3A → MinIO конфиг (и для драйвера, и для экзекуторов)
    spark = (
        SparkSession.builder
        .appName("hw2_load_to_redis")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )
    # дублируем в HadoopConf
    hconf = spark.sparkContext._jsc.hadoopConfiguration()
    hconf.set("fs.s3a.endpoint", MINIO_ENDPOINT)
    hconf.set("fs.s3a.access.key", MINIO_ACCESS)
    hconf.set("fs.s3a.secret.key", MINIO_SECRET)
    hconf.set("fs.s3a.path.style.access", "true")
    hconf.set("fs.s3a.connection.ssl.enabled", "false")
    hconf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    return spark

def _to_py_map(m):
    """Безопасно привести genre_profile к dict[str,float]."""
    if m is None:
        return {}
    if isinstance(m, dict):
        items = m.items()
    else:
        try:
            items = dict(m).items()  # на случай JavaMap
        except Exception:
            return {}
    out = {}
    for k, v in items:
        try:
            out[str(k)] = float(v) if v is not None else 0.0
        except Exception:
            # если Decimal/str и т.п.
            try:
                out[str(k)] = float(str(v))
            except Exception:
                pass
    return out

def write_partition(rows):
    # импорт внутри executors, чтобы не требовать redis на драйвере
    import redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    pipe = r.pipeline(transaction=False)
    n = 0
    for row in rows:
        try:
            payload = {
                "user_id": int(row.user_id),
                "avg_rating": float(row.avg_rating) if row.avg_rating is not None else None,
                "num_movies": int(row.num_movies) if row.num_movies is not None else 0,
                "genre_profile": _to_py_map(getattr(row, "genre_profile", None)),
                "last_interaction_ts": int(row.last_interaction_ts) if row.last_interaction_ts is not None else None,
                "movie_ids": [int(x) for x in (row.movie_ids or [])],
            }
            pipe.set(str(payload["user_id"]), json.dumps(payload))
            n += 1
            if n % 1000 == 0:
                pipe.execute()
        except Exception as e:
            # печать в stdout попадает в worker-лог, но таск не валим из-за одного
            print(f"[load_to_redis] WARN user_id={getattr(row,'user_id',None)}: {e}")
    if n:
        pipe.execute()

def main():
    spark = build_session()
    df = spark.read.parquet(FEATURES_PATH)

    # подчищаем типы и None в genre_profile
    empty_map = F.expr("map()").cast("map<string,double>")
    df = df.withColumn(
        "genre_profile",
        F.when(F.col("genre_profile").isNull(), empty_map).otherwise(F.col("genre_profile"))
    )

    (
        df.select("user_id", "avg_rating", "num_movies", "genre_profile", "last_interaction_ts", "movie_ids")
          .repartition(8)
          .foreachPartition(write_partition)
    )
    spark.stop()

if __name__ == "__main__":
    main()
