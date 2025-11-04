#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="/out"
TMP_DIR="/tmp/ml"
URL_DEFAULT="https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
URL="${MOVIELENS_URL:-$URL_DEFAULT}"

mkdir -p "$OUT_DIR" "$TMP_DIR"

echo
echo "[entrypoint] Загружаем набор данных MovieLens из: $URL"
wget -q -O "$TMP_DIR/ml.zip" "$URL"

echo
echo "[entrypoint] Разархивируем..."
unzip -o -qq "$TMP_DIR/ml.zip" -d "$TMP_DIR"

# Проверка на существование директории
DATA_DIR="$(find "$TMP_DIR" -maxdepth 1 -type d -name 'ml-latest-small' -print -quit)"
if [[ -z "${DATA_DIR}" ]]; then
  echo "[entrypoint] Не найдена директория 'ml-latest-small', переходим в корень tmp"
  DATA_DIR="$TMP_DIR"
fi

# Берем нужные CSV
RATINGS="${DATA_DIR}/ratings.csv"
MOVIES="${DATA_DIR}/movies.csv"

if [[ ! -f "$RATINGS" || ! -f "$MOVIES" ]]; then
  echo "[entrypoint] Файлы ratings.csv и movies.csv не найдены. Выходим."
  exit 2
fi

echo
echo "[entrypoint] Запускаем PySpark задачу..."
spark-submit /app/job.py --ratings "$RATINGS" --movies "$MOVIES" --out "$OUT_DIR/genres_top10.csv"

echo "[entrypoint] Готово. Результат в /out:"
ls -l "$OUT_DIR"
