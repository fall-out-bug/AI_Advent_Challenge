"""Spark training job."""

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("train").getOrCreate()
df = spark.read.parquet("data/train.parquet")
# Training logic here
spark.stop()

