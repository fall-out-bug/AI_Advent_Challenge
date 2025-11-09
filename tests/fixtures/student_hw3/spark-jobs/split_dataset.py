# spark-jobs/split_dataset.py
import os
from pyspark.sql import SparkSession, functions as F, types as T, Window

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
MOVIELENS_PREFIX = os.getenv("MOVIELENS_PREFIX", "latest/")
RAW_OUT = os.getenv("RAW_OUT", "s3a://raw/movielens/")


def build_session():
    spark = (
        SparkSession.builder.appName("hw3_split_dataset")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )
    return spark


def main():
    spark = build_session()
    ratings_path = f"s3a://movielens/{MOVIELENS_PREFIX}ratings.csv"
    schema = T.StructType(
        [
            T.StructField("userId", T.IntegerType(), False),
            T.StructField("movieId", T.IntegerType(), False),
            T.StructField("rating", T.DoubleType(), False),
            T.StructField("timestamp", T.LongType(), False),
        ]
    )
    ratings = (
        spark.read.option("header", True)
        .schema(schema)
        .csv(ratings_path)
        .withColumnRenamed("userId", "user_id")
        .withColumnRenamed("movieId", "movie_id")
        .withColumn("ts", F.col("timestamp").cast("long"))
    )

    w = Window.partitionBy("user_id").orderBy(F.col("ts").asc())
    df = ratings.withColumn("rn", F.row_number().over(w))
    last = df.groupBy("user_id").agg(F.max("rn").alias("max_rn"))
    df = df.join(last, on="user_id", how="left").withColumn(
        "is_test", F.col("rn") == F.col("max_rn")
    )

    train = df.where(~F.col("is_test")).drop("rn", "max_rn", "is_test", "timestamp")
    test = df.where(F.col("is_test")).drop("rn", "max_rn", "is_test", "timestamp")

    (train.write.mode("overwrite").parquet(RAW_OUT + "train/"))
    (test.write.mode("overwrite").parquet(RAW_OUT + "test/"))
    spark.stop()


if __name__ == "__main__":
    main()
