# spark-jobs/features_events.py
import os
from pyspark.sql import SparkSession, functions as F, types as T, Window

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")

SPLIT = os.getenv("SPLIT", "train")
IN_PATH_TRAIN = os.getenv("IN_PATH_TRAIN", "s3a://raw/movielens/train/")
IN_PATH_TEST = os.getenv("IN_PATH_TEST", "s3a://raw/movielens/test/")
OUT_PATH_TRAIN = os.getenv("OUT_PATH_TRAIN", "s3a://features/train/events/")
OUT_PATH_TEST = os.getenv("OUT_PATH_TEST", "s3a://features/test/events/")


def build_session():
    spark = (
        SparkSession.builder.appName("hw3_features_events")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )
    return spark


def fe_train(spark):
    train = spark.read.parquet(IN_PATH_TRAIN)
    # label
    train = train.withColumn("label", (F.col("rating") >= F.lit(4.0)).cast("int"))
    # window across user's history strictly before current row
    w_hist = (
        Window.partitionBy("user_id")
        .orderBy(F.col("ts").asc())
        .rowsBetween(Window.unboundedPreceding, -1)
    )
    feats = (
        train.withColumn("prev_count", F.count("*").over(w_hist))
        .withColumn("prev_avg", F.avg("rating").over(w_hist))
        .withColumn("prev_std", F.stddev_pop("rating").over(w_hist))
        .withColumn("prev_last_ts", F.max("ts").over(w_hist))
    )
    feats = feats.withColumn(
        "recency", (F.col("ts") - F.col("prev_last_ts")).cast("double")
    )
    # Fill cold-start rows where prev_count is null (no history)
    feats = feats.fillna(
        {"prev_count": 0, "prev_avg": 0.0, "prev_std": 0.0, "recency": 1e9}
    )
    out = feats.select(
        "user_id",
        "movie_id",
        "ts",
        "label",
        "prev_count",
        "prev_avg",
        "prev_std",
        "recency",
    )
    out.write.mode("overwrite").parquet(OUT_PATH_TRAIN)


def fe_test(spark):
    train = spark.read.parquet(IN_PATH_TRAIN).select("user_id", "ts", "rating")
    test = spark.read.parquet(IN_PATH_TEST)
    # Per-user aggregates computed on train only
    agg = train.groupBy("user_id").agg(
        F.count("*").alias("prev_count"),
        F.avg("rating").alias("prev_avg"),
        F.stddev_pop("rating").alias("prev_std"),
        F.max("ts").alias("prev_last_ts"),
    )
    test = test.join(agg, on="user_id", how="left")
    test = test.withColumn(
        "recency", (F.col("ts") - F.col("prev_last_ts")).cast("double")
    )
    test = test.fillna(
        {"prev_count": 0, "prev_avg": 0.0, "prev_std": 0.0, "recency": 1e9}
    )
    # label for test (kept in parquet to compare with Redis-based inference later)
    test = test.withColumn("label", (F.col("rating") >= F.lit(4.0)).cast("int"))
    out = test.select(
        "user_id",
        "movie_id",
        "ts",
        "label",
        "prev_count",
        "prev_avg",
        "prev_std",
        "recency",
    )
    out.write.mode("overwrite").parquet(OUT_PATH_TEST)


def main():
    spark = build_session()
    if SPLIT == "train":
        fe_train(spark)
    elif SPLIT == "test":
        fe_test(spark)
    else:
        raise ValueError("SPLIT must be 'train' or 'test'")
    spark.stop()


if __name__ == "__main__":
    main()
