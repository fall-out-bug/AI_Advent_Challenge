#!/usr/bin/env bash
# Создает образ и запускает контейнер, результаты сохраняются в ./output (или в указанную папку через $1)
set -euo pipefail

IMAGE="${IMAGE:-mlsd-hw1}"
OUT_DIR="${1:-output}"

mkdir -p "$OUT_DIR"

echo
echo "[host] Создаем образ: $IMAGE"
docker build -t "$IMAGE" .

echo
echo "[host] Запускаем контейнер..."
docker run --rm -v "$(pwd)/${OUT_DIR}":/out "$IMAGE"

echo
echo "[host] Готово. Итоговый CSV: ${OUT_DIR}/genres_top10.csv"
