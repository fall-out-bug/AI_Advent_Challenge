#!/usr/bin/env bash
set -euo pipefail

# ========== Config ==========
DAG_ID="mlsd_hw3"
API_USER="hw3user"
API_PASS="hw3pass"
AIRFLOW_URL="http://airflow:8080"
MLFLOW_PORT="${MLFLOW_PORT:-5000}"
MLFLOW_SERVE_PORT="${MLFLOW_SERVE_PORT:-6000}"
MODEL_NAME="${MODEL_NAME:-mlsd_hw3_model}"
export MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
export MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin}"

# -------- helpers --------
die() { echo "ERROR: $*" >&2; exit 1; }

wait_healthy() {
  local svc="$1" timeout="${2:-60}"   # по умолчанию 1 минута
  echo "Ожидание healthy-статуса сервиса '$svc' (таймаут ${timeout}s)..."
  local cid
  cid="$(docker compose ps -q "$svc")" || die "сервис '$svc' не найден"
  local start=$(date +%s)
  while true; do
    local status
    status="$(docker inspect -f '{{ if .State.Health }}{{ .State.Health.Status }}{{ else }}unknown{{ end }}' "$cid")" || true
    if [[ "$status" == "healthy" ]]; then
      echo "    ✅ Сервис '$svc' теперь healthy"
      return 0
    fi
    if (( $(date +%s) - start > timeout )); then
      echo "    ❌ '$svc' healthcheck timed out. Last logs:"
      docker compose logs --no-color --tail=200 "$svc" || true
      exit 1
    fi
    sleep 2
  done
}

echo
echo "[1/12] Создание образов..."
docker compose build

echo
echo "[2/12] Запуск оркестра..."
docker compose up -d

echo
wait_healthy minio  30
wait_healthy redis  30
wait_healthy spark-master 30
wait_healthy spark-worker-1 30
wait_healthy mlflow 60
wait_healthy airflow 240

echo
echo "[3/12] Создаю/синхронизирую API-пользователя ${API_USER} в Airflow..."
docker compose exec airflow bash -lc "
  set -e
  if ! airflow users list | awk 'NR>2{print \$1}' | grep -qx '${API_PASS}'; then
    airflow users create \
      --username '${API_USER}' \
      --password '${API_PASS}' \
      --firstname HW3 \
      --lastname User \
      --role Admin \
      --email GavrisAS@exam.com
  else
    # На 2.9.x работает update; если в вашей сборке нет, упадёт — поймаем ниже
    airflow users update --username '${API_USER}' --password '${API_PASS}' || \
    airflow users set-password --username '${API_USER}' --password '${API_PASS}' || true
  fi
"

echo
echo "[4/12] Проверяю доступ к Airflow API по BasicAuth..."
docker compose exec airflow bash -lc "curl -fsS -u '${API_USER}:${API_PASS}' ${AIRFLOW_URL}/api/v1/health | grep -q healthy" \
  || { echo '❌ BasicAuth к Airflow API не прошёл (ожидали {"status":"healthy"}).'; exit 1; }
echo "✅ Airflow API отвечает и авторизация работает."


# -------- Запускаем DAG --------
RUN_ID="hw3_$(date -u +%Y%m%dT%H%M%SZ)"
echo
echo "[5/12] Запускаем DAG ${DAG_ID} с run_id=${RUN_ID} ..."
docker compose exec airflow bash -lc \
  "curl -fsS -u '${API_USER}:${API_PASS}' -H 'Content-Type: application/json' \
   -d '{\"dag_run_id\":\"${RUN_ID}\"}' ${AIRFLOW_URL}/api/v1/dags/${DAG_ID}/dagRuns > /dev/null"


# -------- 6) poll DAG run state via REST API (BasicAuth) --------
echo
echo "[6/12] Ожидаем завершение DAG ${DAG_ID} (run_id=${RUN_ID})..."
ATTEMPTS=300   # до 10 минут (1s * 600)

for i in $(seq 1 $ATTEMPTS); do
  # читаем JSON и достаем .state надёжно (без grep|sed)
  state=$(
    docker compose run --rm airflow bash -lc \
      "curl -fsS -u ${API_USER}:${API_PASS} -H 'Accept: application/json' \
        ${AIRFLOW_URL}/api/v1/dags/${DAG_ID}/dagRuns/${RUN_ID} \
      | python3 -c 'import sys,json; sys.stdout.write(json.load(sys.stdin).get(\"state\",\" \").strip())'" \
    2>/dev/null || true
  )

  # safety: убрать любые \r и \n, которые могли проскочить
  state="${state//$'\r'/}"
  state="${state//$'\n'/}"

  if [[ \"$state\" == \"success\" ]]; then
    echo \"✅ DAG run ${RUN_ID} finished with SUCCESS.\"
    break
  elif [[ \"$state\" == \"failed\" ]]; then
    echo \"❌ DAG run ${RUN_ID} FAILED. Recent task states:\"
    docker compose run --rm airflow airflow tasks states-for-dag-run --dag-run-id "$RUN_ID" || true
    exit 1
  fi

  # чтобы не молчать — каждые 5s подсветим текущий статус
  if (( i % 5 == 0 )); then
    printf "Still running... state='%s' (try %s/%s)\n" "${state:-unknown}" "$i" "$ATTEMPTS"
  fi
  sleep 1
done

# safety: если так и не дождались SUCCESS — покажем ответ API и упадём
#if [[ \"${state:-}\" != \"success\" ]]; then
#  echo \"Ответ API (для отладки):\"
#  docker compose run --rm airflow bash -lc \
#    \"curl -i -u ${API_USER}:${API_PASS} -H 'Accept: application/json' \
#      ${AIRFLOW_URL}/api/v1/dags/${DAG_ID}/dagRuns/${RUN_ID} || true\"
#  die \"Timeout waiting for DAG run ${RUN_ID} (last state='${state:-unknown}')\"
#fi

# Проверка Redis после успешного DAG
PREFIX="${KEY_PREFIX:-mlsd:test:user}"
DB="${REDIS_DB:-0}"

echo
echo "[7/12] Checking Redis keys with prefix '${PREFIX}:' on DB ${DB} ..."
docker compose exec -T redis sh -lc "redis-cli -n ${DB} --scan --pattern '${PREFIX}:*' | head -n 5"

COUNT=$(docker compose exec -T redis sh -lc \
  "redis-cli -n ${DB} --scan --pattern '${PREFIX}:*' | wc -l | awk '{print \$1}'" \
  | tr -d '\r')

META=$(docker compose exec -T redis sh -lc \
  "redis-cli -n ${DB} HGETALL '${PREFIX}:meta' | tr '\n' ' '" \
  | tr -d '\r')

if [ -z "$COUNT" ] || [ "$COUNT" = "0" ]; then
  echo "ERROR: ❌ Redis check failed: no keys found for pattern '${PREFIX}:*' on DB ${DB}."
  echo "Meta: ${META}"
  exit 1
else
  echo "✅ Redis has ${COUNT} keys for '${PREFIX}:*'."
  echo "Meta: ${META}"
fi

# -------- Размещаем модель в MLFlow --------
echo
echo "[8/12] Attempting to start MLflow serving for Production model '${MODEL_NAME}' on :${MLFLOW_SERVE_PORT}"
docker compose exec -T mlflow bash -lc '
  set -e
  python - <<PY
import mlflow, os
from mlflow.tracking import MlflowClient
mlflow.set_tracking_uri("http://mlflow:5000")
client = MlflowClient()
name = os.environ.get("MODEL_NAME","'${MODEL_NAME}'")
vers = client.get_latest_versions(name, stages=["Production"])
print(vers[0].version if vers else "")
PY
' | {
  read -r version
  if [[ -n "$version" ]]; then
    docker compose exec -T mlflow bash -lc "nohup mlflow models serve -m '''models:/'"${MODEL_NAME}"'/Production''' --host 0.0.0.0 --port '${MLFLOW_SERVE_PORT}' >/tmp/serve.log 2>&1 &"
    echo "✅ Serving started for ${MODEL_NAME} (Production). Port ${MLFLOW_SERVE_PORT}."
  else
    echo "❌ No Production version found; skipping serve."
  fi
}

# --- Wait for MLflow UI, model in Production, and serving port to be ready ---
wait_http_200() {
  # $1 = URL
  local url="$1"
  local max_tries="${2:-60}"   # 60 * 2s = 2 minutes by default
  local i=1
  while [ "$i" -le "$max_tries" ]; do
    # Ask for just the status code; avoid CORS/Host mistakes by using 127.0.0.1
    code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)"
    if [ "$code" = "200" ]; then
      return 0
    fi
    sleep 2
    i=$((i+1))
  done
  return 1
}

wait_model_in_production() {
  # $1 = model name
  local name="$1"
  local url="http://127.0.0.1:${MLFLOW_PORT:-5000}/api/2.0/mlflow/registered-models/get-latest-versions"
  local max_tries="${2:-120}"  # 120 * 2s = 4 minutes
  local i=1
  while [ "$i" -le "$max_tries" ]; do
    # We do NOT --fail here because 404 is common until the model exists; instead parse the body + status
    resp="$(mktemp)"
    code="$(curl -s -H "Content-Type: application/json" -X POST -d "{\"name\":\"$name\",\"stages\":[\"Production\"]}" "$url" -o "$resp" -w "%{http_code}" || true)"
    if [ "$code" = "200" ] && grep -q '"version"' "$resp"; then
      rm -f "$resp"
      return 0
    fi
    rm -f "$resp"
    sleep 2
    i=$((i+1))
  done
  return 1
}

wait_tcp_port() {
  # $1 = host, $2 = port
  local host="$1"
  local port="$2"
  local max_tries="${3:-120}"  # 120 * 1s = 2 minutes
  local i=1
  while [ "$i" -le "$max_tries" ]; do
    # Bash's /dev/tcp works in most shells used on Linux VMs; no netcat required
    (echo > /dev/tcp/"$host"/"$port") >/dev/null 2>&1 && return 0
    sleep 1
    i=$((i+1))
  done
  return 1
}

echo "[9/12] Жду готовности MLflow UI на портe ${MLFLOW_PORT:-5000}..."
wait_http_200 "http://127.0.0.1:${MLFLOW_PORT:-5000}/" 90 || { echo "❌ MLflow UI не ответил 200 за отведённое время"; exit 1; }
echo "✅ MLflow UI отвечает."

echo "[10/12] Жду появления модели '${MODEL_NAME:-mlsd_hw3_model}' в стадии Production..."
wait_model_in_production "${MODEL_NAME:-mlsd_hw3_model}" 180 || { echo "❌ Модель не стала Production за отведённое время"; exit 1; }
echo "✅ Модель в стадии Production найдена."

echo "[11/12] Жду, пока откроется порт сервинга ${MLFLOW_SERVE_PORT:-6000}..."
wait_tcp_port "127.0.0.1" "${MLFLOW_SERVE_PORT:-6000}" 180 || { echo "❌ Порт сервинга ${MLFLOW_SERVE_PORT:-6000} так и не открылся"; exit 1; }
echo "✅ Порт ${MLFLOW_SERVE_PORT:-6000} открыт, сервинг готов."
# --- End of wait block ---

echo
echo "[12/12] Оркестр собран и играет."
echo ""
echo "Точки доступа:"
echo "  - MinIO Console:   http://localhost:9001 (user: $MINIO_ROOT_USER, pass: $MINIO_ROOT_PASSWORD)"
echo "  - Spark Master UI: http://localhost:8080"
echo "  - Spark Worker UI: http://localhost:8081"
echo "  - Airflow UI:      http://localhost:8088 (user: $API_USER, pass: $API_PASS)"
echo "  - MLflow UI:       http://localhost:5000"
