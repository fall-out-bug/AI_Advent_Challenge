#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:-master}"

# Общие переменные (с разумными дефолтами)
export SPARK_HOME="${SPARK_HOME:-/opt/spark}"
export SPARK_MASTER_HOST="${SPARK_MASTER_HOST:-0.0.0.0}"
export SPARK_MASTER_PORT="${SPARK_MASTER_PORT:-7077}"
export SPARK_MASTER_WEBUI_PORT="${SPARK_MASTER_WEBUI_PORT:-8080}"
export SPARK_WORKER_WEBUI_PORT="${SPARK_WORKER_WEBUI_PORT:-8081}"
export SPARK_MASTER_URL="${SPARK_MASTER_URL:-spark://spark-master:${SPARK_MASTER_PORT}}"

# На всякий: чтобы Spark не подхватил странный localhost
export SPARK_LOCAL_IP="${SPARK_LOCAL_IP:-0.0.0.0}"

echo "[entrypoint] ROLE=$ROLE"
echo "[entrypoint] SPARK_MASTER_HOST=$SPARK_MASTER_HOST"
echo "[entrypoint] SPARK_MASTER_PORT=$SPARK_MASTER_PORT"
echo "[entrypoint] SPARK_MASTER_WEBUI_PORT=$SPARK_MASTER_WEBUI_PORT"
echo "[entrypoint] SPARK_WORKER_WEBUI_PORT=$SPARK_WORKER_WEBUI_PORT"
echo "[entrypoint] SPARK_MASTER_URL=$SPARK_MASTER_URL"

# ВАЖНО: НИКАКИХ sbin/start-*.sh — запускаем только ОДИН процесс через exec
if [[ "$ROLE" == "master" ]]; then
  exec "${SPARK_HOME}/bin/spark-class" org.apache.spark.deploy.master.Master \
    --host "${SPARK_MASTER_HOST}" \
    --port "${SPARK_MASTER_PORT}" \
    --webui-port "${SPARK_MASTER_WEBUI_PORT}"

elif [[ "$ROLE" == "worker" ]]; then
  # опционально пробросим cores/memory флагами, если заданы через env
  ARGS=()
  [[ -n "${SPARK_WORKER_CORES:-}"  ]] && ARGS+=( --cores  "${SPARK_WORKER_CORES}" )
  [[ -n "${SPARK_WORKER_MEMORY:-}" ]] && ARGS+=( --memory "${SPARK_WORKER_MEMORY}" )
  ARGS+=( --webui-port "${SPARK_WORKER_WEBUI_PORT}" )
  exec "${SPARK_HOME}/bin/spark-class" org.apache.spark.deploy.worker.Worker \
    "${ARGS[@]}" \
    "${SPARK_MASTER_URL}"

else
  echo "[entrypoint] Unknown role: $ROLE; executing raw command: $*"
  exec "$@"
fi
