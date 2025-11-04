# MLSD HW2

## Старт
```bash
./run.sh
```
UI:
- MinIO: http://localhost:9001  (логин/пароль см. в run.sh)
- Spark Master: http://localhost:8080
- Spark Worker: http://localhost:8081
- Airflow: http://localhost:8088

## DAG `mlsd_hw2`
Пайплайн:
1) `get_dataset`: скачать и распаковать MovieLens
2) `put_dataset`: загрузить CSV в MinIO (bucket `movielens`)
3) `features_engineering`: Spark читает `s3a://movielens/...`, пишет фичи в `s3a://features/users/` (Parquet)
4) `load_features`: читает Parquet из MinIO и кладёт JSON по ключу `user_id` в Redis.

