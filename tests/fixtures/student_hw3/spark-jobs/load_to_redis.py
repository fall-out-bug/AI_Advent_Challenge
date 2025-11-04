# spark-jobs/load_to_redis.py
import os, json
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.utils import AnalysisException

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS   = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB   = int(os.getenv("REDIS_DB", "0"))
KEY_PREFIX = os.getenv("KEY_PREFIX", "mlsd:test:user")

FEATURES_PATH = os.getenv("FEATURES_PATH", "s3a://features/test/events/")

def build_session():
    # S3A → MinIO конфиг (и для драйвера, и для экзекуторов)
    spark = (
        SparkSession.builder
        .appName("hw3_load_to_redis")
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

def write_partition(rows):
    # Импорт внутри экзекьютора
    import redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True, socket_keepalive=True)
    pipe = r.pipeline(transaction=False)
    n = 0
    for row in rows:
        key = f"{KEY_PREFIX}:{int(row['user_id'])}"
        payload = {
            "prev_count": float(row['prev_count'] or 0.0),
            "prev_avg": float(row['prev_avg'] or 0.0),
            "prev_std": float(row['prev_std'] or 0.0),
            "recency": float(row['recency'] or 0.0),
        }
        pipe.set(key, json.dumps(payload))
        n += 1
        if n % 1000 == 0:
            pipe.execute()
    if n % 1000 != 0:
        pipe.execute()

def main():
    spark = build_session()
    try:
        df = spark.read.parquet(FEATURES_PATH).select("user_id","prev_count","prev_avg","prev_std","recency")
    except AnalysisException as e:
        raise RuntimeError(f"Cannot read FEATURES_PATH={FEATURES_PATH}: {e}")
    total_users = df.select("user_id").distinct().count()
    if total_users == 0:
        raise RuntimeError(f"No test features to load (FEATURES_PATH={FEATURES_PATH}). Failing task.")
    # Пишем фичи в Redis
    df.repartition(8).foreachPartition(write_partition)

    # Пишем «маячок» ТАКЖЕ на экзекьюторе (а не в драйвере)
    total_bc = spark.sparkContext.broadcast(int(total_users))
    def write_meta(_):
        import redis, time
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        r.hset(f"{KEY_PREFIX}:meta", mapping={"users": total_bc.value, "ts": int(time.time())})
    spark.sparkContext.parallelize([1], 1).foreachPartition(write_meta)

    spark.stop()

if __name__ == "__main__":
    main()
