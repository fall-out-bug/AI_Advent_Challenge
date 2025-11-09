# /opt/airflow/spark-jobs/features_engineering.py
import os
from pyspark.sql import SparkSession, Window
import pyspark.sql.functions as F
from pyspark import StorageLevel

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

RATINGS_PATH = os.getenv("RATINGS_PATH", "s3a://movielens/latest/ratings.csv")
MOVIES_PATH = os.getenv("MOVIES_PATH", "s3a://movielens/latest/movies.csv")
OUT_PATH = os.getenv("OUT_PATH", "s3a://features/users")

OUT_PARTS = int(os.getenv("FE_OUT_PARTITIONS", "200"))  # разумное число файлов
SHUFFLE_PARTS = int(os.getenv("SPARK_SHUFFLE_PARTITIONS", "400"))

builder = (
    SparkSession.builder.appName("hw2_features_engineering")
    # S3A / MinIO
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", MINIO_KEY)
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config("spark.hadoop.fs.s3a.fast.upload", "true")
    # Исполнитель/память — из DAG, но на всякий случай пусть будут дефолты
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    # Тюнинг шафла/входных партиций
    .config("spark.sql.adaptive.enabled", "true")
    .config("spark.sql.shuffle.partitions", str(SHUFFLE_PARTS))
    .config("spark.sql.files.maxPartitionBytes", str(128 * 1024 * 1024))  # 128MB
    .config("spark.reducer.maxSizeInFlight", "24m")
    .config("spark.shuffle.file.buffer", "32k")
)

spark = builder.getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Чтение
ratings = (
    spark.read.option("header", True)
    .csv(RATINGS_PATH)
    .select(
        F.col("userId").cast("int").alias("userId"),
        F.col("movieId").cast("int").alias("movieId"),
        F.col("rating").cast("double").alias("rating"),
        F.col("timestamp").cast("long").alias("ts"),
    )
)

movies = (
    spark.read.option("header", True)
    .csv(MOVIES_PATH)
    .select(
        F.col("movieId").cast("int").alias("movieId"),
        F.col("title").alias("title"),
        F.col("genres").alias("genres"),
    )
)

# Базовая статистика по пользователю (без тяжёлых списков)
user_stats = ratings.groupBy("userId").agg(
    F.count("*").alias("ratings_cnt"),
    F.mean("rating").alias("rating_mean"),
    F.expr("percentile_approx(rating, 0.5)").alias("rating_median"),
    F.stddev_pop("rating").alias("rating_std"),
    F.max("ts").alias("last_ts"),
)

# Любимый жанр: explode -> count -> top1 per user
genres_long = (
    ratings.join(movies.select("movieId", "genres"), "movieId", "left")
    .withColumn("genre", F.explode_outer(F.split(F.col("genres"), "\\|")))
    .select("userId", "genre")
    .where(F.col("genre").isNotNull() & (F.col("genre") != "(no genres listed)"))
)

genre_cnt = genres_long.groupBy("userId", "genre").count()

w = Window.partitionBy("userId").orderBy(F.col("count").desc(), F.col("genre").asc())
fav_genre = (
    genre_cnt.withColumn("rn", F.row_number().over(w))
    .where(F.col("rn") == 1)
    .select(
        "userId",
        F.col("genre").alias("fav_genre"),
        F.col("count").alias("fav_genre_cnt"),
    )
)

features = user_stats.alias("u").join(fav_genre.alias("g"), "userId", "left")

# Пишем компактно: без репартиции по ключу, просто укрупняем число файлов
(
    features.coalesce(OUT_PARTS)
    .write.mode("overwrite")
    .option("maxRecordsPerFile", 100_000)
    .parquet(OUT_PATH)
)

spark.stop()
