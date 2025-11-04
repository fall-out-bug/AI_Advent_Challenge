# spark-jobs/features_engineering.py
import os
from pyspark.sql import SparkSession, functions as F, types as T
from pyspark import StorageLevel

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS   = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET   = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

OUT_PATH  = os.getenv("FEATURES_OUT", "s3a://features/users/")
OUT_PARTS = int(os.getenv("FE_OUT_PARTITIONS", "256"))  # было 64 → подняли до 256
SHUFFLE_PARTS = int(os.getenv("SPARK_SHUFFLE_PARTITIONS", "1024"))  # было 256 → подняли до 1024

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
        # MinIO / S3A
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.fast.upload", "true")
        .config("spark.hadoop.fs.s3a.fast.upload.buffer", "disk")
        .config("spark.hadoop.fs.s3a.buffer.dir", "/tmp/s3a-buf")
        # --- Надёжная запись на S3A ---
        .config("spark.sql.sources.commitProtocolClass", "org.apache.spark.internal.io.cloud.PathOutputCommitProtocol")
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
        .config("spark.hadoop.fs.s3a.committer.name", "directory")
        .config("spark.hadoop.fs.s3a.committer.staging.tmp.path", "/tmp/s3a")
        .config("spark.hadoop.parquet.enable.summary-metadata", "false")
        # Shuffle / SQL / Memory
        .config("spark.sql.shuffle.partitions", str(SHUFFLE_PARTS))
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .config("spark.sql.adaptive.shuffle.targetPostShuffleInputSize", "134217728")  # 128MB
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")  # не используем pandas/Arrow
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.sql.files.maxRecordsPerFile", "3000000")
        # --- Диск для спиллов/темпа ---
        .config("spark.local.dir", "/tmp/spark-tmp")
        # --- Параметры сети/коннектов к S3A (чуть шире дефолтов) ---
        .config("spark.hadoop.fs.s3a.connection.maximum", "64")
        .config("spark.hadoop.fs.s3a.threads.max", "64")
        .config("spark.hadoop.fs.s3a.max.total.tasks", "128")
        .getOrCreate()
    )
    # продублируем в HadoopConf
    hconf = spark.sparkContext._jsc.hadoopConfiguration()
    hconf.set("fs.s3a.endpoint", MINIO_ENDPOINT)
    hconf.set("fs.s3a.access.key", MINIO_ACCESS)
    hconf.set("fs.s3a.secret.key", MINIO_SECRET)
    hconf.set("fs.s3a.path.style.access", "true")
    hconf.set("fs.s3a.connection.ssl.enabled", "false")
    hconf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hconf.set("fs.s3a.fast.upload", "true")
    hconf.set("fs.s3a.fast.upload.buffer", "disk")
    hconf.set("fs.s3a.buffer.dir", "/tmp/s3a-buf")
    hconf.set("mapreduce.fileoutputcommitter.algorithm.version", "2")
    hconf.set("fs.s3a.committer.name", "directory")
    hconf.set("fs.s3a.committer.staging.tmp.path", "/tmp/s3a")
    hconf.set("parquet.enable.summary-metadata", "false")
    return spark

def main():
    spark = build_session()

    ratings_path = "s3a://movielens/latest/ratings.csv"
    movies_path  = "s3a://movielens/latest/movies.csv"

    # Ratings: берём только нужные поля, партишеним по user_id
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
        .repartition(SHUFFLE_PARTS)
        .persist(StorageLevel.MEMORY_AND_DISK)
    )
    # Базовые агрегаты на пользователя
    agg_basic = (ratings
        .groupBy("user_id")
        .agg(
            F.avg("rating").alias("avg_rating"),
            F.countDistinct("movie_id").alias("num_movies"),
            F.max("ts").alias("last_interaction_ts"),
            F.array_sort(F.collect_set(F.col("movie_id").cast("int"))).alias("movie_ids"),
        )
    ).persist(StorageLevel.MEMORY_AND_DISK)

    # Movies: маленькая таблица, взорвём жанры в строки и заброскастим
    movies = (spark.read
        .option("header", True)
        .schema(SCHEMA_MOVIES)
        .csv(movies_path)
        .select(F.col("movieId").alias("movie_id"), F.col("genres"))
    )

    genre_map = (movies
        .withColumn("genre", F.explode(F.split(F.col("genres"), "\\|")))
        .where(F.col("genre").isNotNull() & (F.col("genre") != "(no genres listed)"))
        .select("movie_id", "genre")
        .dropDuplicates(["movie_id", "genre"])
    )

    from pyspark.sql.functions import broadcast
    genre_map = broadcast(genre_map)

    # user-genre счётчики через join (только (user_id, movie_id) из ratings)
    user_movie = ratings.select("user_id","movie_id").dropDuplicates()
    per_genre = (user_movie
        .join(genre_map, on="movie_id", how="inner")
        .groupBy("user_id", "genre").agg(F.count(F.lit(1)).alias("cnt"))
        .repartition(SHUFFLE_PARTS, "user_id")
        .persist(StorageLevel.MEMORY_AND_DISK)
    )

    totals = per_genre.groupBy("user_id").agg(F.sum("cnt").alias("total"))
    per_genre = (per_genre.join(totals, on="user_id", how="left")
                 .withColumn("pct", F.col("cnt")/F.col("total")))

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

    # Сколько крупных файлов писать (можно управлять через FE_WRITE_PARTS)
    WRITE_PARTS = int(os.getenv("FE_WRITE_PARTS", "64"))

    (features
        .select("user_id","avg_rating","num_movies","genre_profile","last_interaction_ts","movie_ids")
        .coalesce(WRITE_PARTS)  # укрупняем файлы → меньше метаданных и шансов потерять блок
        .write.mode("overwrite")
        .option("compression","snappy")
        .parquet(OUT_PATH)
    )

    # чистим кеши
    per_genre.unpersist(False)
    agg_basic.unpersist(False)
    ratings.unpersist(False)
    spark.catalog.clearCache()
    spark.stop()

if __name__ == "__main__":
    main()
