# spark-jobs/features_engineering.py
import os
from pyspark.sql import SparkSession, functions as F, types as T
from pyspark import StorageLevel

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS   = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

# Параметры, которыми удобно рулить снаружи
OUT_PATH   = os.getenv("FEATURES_OUT", "s3a://features/users/")
WRITE_PARTS = int(os.getenv("FE_WRITE_PARTS", "96"))           # сколько крупных файлов писать
SHUFFLE_PARTS = int(os.getenv("SPARK_SHUFFLE_PARTITIONS", "256"))
MAX_REC_PER_FILE = int(os.getenv("FE_MAX_RECORDS_PER_FILE", "250000"))

SCHEMA_RATINGS = T.StructType([
    T.StructField("userId",   T.IntegerType(), True),
    T.StructField("movieId",  T.IntegerType(), True),
    T.StructField("rating",   T.DoubleType(),  True),
    T.StructField("timestamp",T.LongType(),    True),
])
SCHEMA_MOVIES = T.StructType([
    T.StructField("movieId",  T.IntegerType(), True),
    T.StructField("title",    T.StringType(),  True),
    T.StructField("genres",   T.StringType(),  True),
])

def build_session():
    spark = (SparkSession.builder
        .appName("hw2_features_engineering")
        # S3A → MinIO
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.fast.upload", "true")
        # SQL/Shuffle
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.shuffle.partitions", str(SHUFFLE_PARTS))
        .config("spark.sql.files.maxPartitionBytes", str(128 * 1024 * 1024))  # 128MB
        # На всякий случай более бережные буферы шафла
        .config("spark.reducer.maxSizeInFlight", "24m")
        .config("spark.shuffle.file.buffer", "32k")
        .getOrCreate()
    )
    # продублируем в HadoopConf (иногда помогает)
    hconf = spark.sparkContext._jsc.hadoopConfiguration()
    hconf.set("fs.s3a.endpoint", MINIO_ENDPOINT)
    hconf.set("fs.s3a.access.key", MINIO_ACCESS)
    hconf.set("fs.s3a.secret.key", MINIO_SECRET)
    hconf.set("fs.s3a.path.style.access", "true")
    hconf.set("fs.s3a.connection.ssl.enabled", "false")
    hconf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    return spark

def main():
    spark = build_session()
    spark.sparkContext.setLogLevel("WARN")

    ratings_path = "s3a://movielens/latest/ratings.csv"
    movies_path  = "s3a://movielens/latest/movies.csv"

    # читаем с явной схемой → меньше оверхеда и памяти
    ratings = (spark.read
        .option("header", True)
        .schema(SCHEMA_RATINGS)
        .csv(ratings_path)
        .select(
            F.col("userId").alias("user_id"),
            F.col("movieId").alias("movie_id"),
            F.col("rating"),
            F.col("timestamp").alias("ts"),
        )
        .dropna(subset=["user_id","movie_id","rating","ts"])
    )
    # Вместо key-repartition тут оставляем Sparkу свободу + кэш на диск
    ratings = ratings.repartition(SHUFFLE_PARTS).persist(StorageLevel.DISK_ONLY)

    # movies маленькая — отдадим её в broadcast
    movies = (spark.read
        .option("header", True)
        .schema(SCHEMA_MOVIES)
        .csv(movies_path)
        .select(
            F.col("movieId").alias("movie_id"),
            F.col("title"),
            F.col("genres"),
        )
    )
    from pyspark.sql.functions import broadcast
    movies = broadcast(movies)

    # базовые агрегаты на пользователя
    agg_basic = (ratings
        .groupBy("user_id")
        .agg(
            F.avg("rating").alias("avg_rating"),
            F.countDistinct("movie_id").alias("num_movies"),
            F.max("ts").alias("last_interaction_ts"),
            F.array_sort(F.collect_set(F.col("movie_id").cast("int"))).alias("movie_ids"),
        )
    )

    # профиль по жанрам
    joined = ratings.join(movies, on="movie_id", how="left").select("user_id", "movie_id", "genres")
    genre_arr = F.split(F.col("genres"), "\\|")
    exploded = (joined
        .withColumn("genre", F.explode(genre_arr))
        .where(F.col("genre").isNotNull() & (F.col("genre") != "(no genres listed)"))
        .select("user_id", "movie_id", "genre")
        .dropDuplicates(["user_id", "movie_id", "genre"])
    ).persist(StorageLevel.DISK_ONLY)

    per_genre = exploded.groupBy("user_id", "genre").agg(F.count(F.lit(1)).alias("cnt")).persist(StorageLevel.DISK_ONLY)
    totals = per_genre.groupBy("user_id").agg(F.sum("cnt").alias("total"))
    per_genre = per_genre.join(totals, on="user_id", how="left").withColumn("pct", F.col("cnt")/F.col("total"))

    genre_profile = (per_genre.groupBy("user_id")
        .agg(F.map_from_arrays(F.collect_list("genre"), F.collect_list(F.round("pct", 6))).alias("genre_profile"))
    )

    features = (agg_basic.join(genre_profile, on="user_id", how="left"))

    # для пустых карт
    empty_map = F.expr("map()").cast("map<string,double>")
    features = features.withColumn(
        "genre_profile",
        F.when(F.col("genre_profile").isNull(), empty_map).otherwise(F.col("genre_profile"))
    )

    # --- Ключевая правка: НЕТ финальной repartition по ключу ---
    # Крупнее файлы, меньше коммитов → стабильнее запись на MinIO
    (features
        .select("user_id","avg_rating","num_movies","genre_profile","last_interaction_ts","movie_ids")
        .coalesce(WRITE_PARTS)
        .write
        .mode("overwrite")
        .option("compression", "snappy")
        .option("maxRecordsPerFile", MAX_REC_PER_FILE)
        .parquet(OUT_PATH)
    )

    spark.stop()

if __name__ == "__main__":
    main()
