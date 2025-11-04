#!/usr/bin/env python3
import argparse, os, shutil, tempfile
from pyspark.sql import SparkSession, functions as F

def compute_top10_genres(spark, ratings_csv, movies_csv):
    # Загружаем CSV
    ratings = spark.read.csv(ratings_csv, header=True, inferSchema=True)
    movies = spark.read.csv(movies_csv, header=True, inferSchema=True)

    # Объединяем по movieId
    joined = ratings.join(movies, on='movieId', how='inner')

    # Объединяем мультижанровые поля как "Adventure|Comedy" -> строки
    # Исключаем '(no genres listed)' из статистики
    exploded = (
        joined
        .withColumn('genre', F.explode(F.split(F.col('genres'), '\\|')))
        .filter(F.col('genre').isNotNull() & (F.col('genre') != '(no genres listed)') & (F.col('genre') != ''))
    )

    # Считаем отзывы по жанрам
    counts = exploded.groupBy('genre').agg(F.count(F.lit(1)).alias('num_ratings'))

    # Топ-10 жанров по отзывам
    top10 = counts.orderBy(F.desc('num_ratings'), F.asc('genre')).limit(10)

    return top10.select('genre', 'num_ratings')

def write_single_csv(df, out_csv_path):
    tmp_dir = tempfile.mkdtemp(prefix='genres_out_')
    # Записываем как один раздел
    df.coalesce(1).write.mode('overwrite').option('header', True).csv(tmp_dir)

    # Перемещаем в финальный путь
    part_file = None
    for root, _, files in os.walk(tmp_dir):
        for f in files:
            if f.startswith('part-') and f.endswith('.csv'):
                part_file = os.path.join(root, f)
                break
        if part_file:
            break

    if not part_file:
        raise RuntimeError('Не удалось найти часть Spark файла для вывода CSV.')

    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)
    # Если существует, заменяем
    if os.path.exists(out_csv_path):
        os.remove(out_csv_path)
    shutil.move(part_file, out_csv_path)

    # Очищаем Spark директории с метаданными
    shutil.rmtree(tmp_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description='Вычисляем top-10 жанров по отзывам (MovieLens) используя PySpark.')
    parser.add_argument('--ratings', required=True, help='Путь к ratings.csv')
    parser.add_argument('--movies', required=True, help='Путь к movies.csv')
    parser.add_argument('--out', required=True, help='Путь к результату (файл CSV)')
    args = parser.parse_args()

    spark = (
        SparkSession.builder
        .appName('mlsd-hw1-genres')
        .master('local[*]')
        .config('spark.sql.shuffle.partitions', '8')
        .getOrCreate()
    )

    try:
        result = compute_top10_genres(spark, args.ratings, args.movies)
        write_single_csv(result, args.out)
        print(f'[job] Записал CSV файл в: {args.out}')
    finally:
        spark.stop()

if __name__ == '__main__':
    main()
