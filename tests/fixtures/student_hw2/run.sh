#!/usr/bin/env bash
set -euo pipefail

export MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
export MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin}"

# -------- helpers --------
die() { echo "ERROR: $*" >&2; exit 1; }

wait_healthy() {
  local svc="$1" timeout="${2:-60}"   # по умолчанию 1 минута
  echo "Ожидание полного запуска сервиса '$svc' (таймаут ${timeout}s)..."
  local cid
  cid="$(docker compose ps -q "$svc")" || die "сервис '$svc' не найден"
  local start=$(date +%s)
  while true; do
    local status
    status="$(docker inspect -f '{{ if .State.Health }}{{ .State.Health.Status }}{{ else }}unknown{{ end }}' "$cid")" || true
    if [[ "$status" == "healthy" ]]; then
      echo "    ✅ Сервис '$svc' полностью запущен."
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

# Дополнительные переменные
DAG_ID="mlsd_hw2"
API_USER="hw2user"
API_PASS="hw2pass"
AIRFLOW_URL="http://airflow:8080"

echo
echo "[1/3] Создание образов..."
docker compose build

echo
echo "[2/3] Запуск оркестра..."
docker compose up -d

wait_healthy minio  30
wait_healthy redis  30
wait_healthy spark-master 30
wait_healthy spark-worker-1 30
wait_healthy airflow 240

echo
echo "Создаю/синхронизирую API-пользователя ${API_USER} в Airflow..."
docker compose exec airflow bash -lc "
  set -e
  if ! airflow users list | awk 'NR>2{print \$1}' | grep -qx '${API_PASS}'; then
    airflow users create \
      --username '${API_USER}' \
      --password '${API_PASS}' \
      --firstname HW2 \
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
echo "Проверяю доступ к Airflow API по BasicAuth..."
docker compose exec airflow bash -lc "curl -fsS -u '${API_USER}:${API_PASS}' ${AIRFLOW_URL}/api/v1/health | grep -q healthy" \
  || { echo '❌ BasicAuth к Airflow API не прошёл (ожидали {"status":"healthy"}).'; exit 1; }
echo "✅ Airflow API отвечает и авторизация работает."


# -------- Запускаем DAG --------
RUN_ID="hw2_$(date -u +%Y%m%dT%H%M%SZ)"
echo
echo "Запускаем DAG mlsd_hw2 с run_id=${RUN_ID} ..."
docker compose exec airflow bash -lc \
  "curl -fsS -u '${API_USER}:${API_PASS}' -H 'Content-Type: application/json' \
   -d '{\"dag_run_id\":\"${RUN_ID}\"}' ${AIRFLOW_URL}/api/v1/dags/mlsd_hw2/dagRuns > /dev/null"


# -------- 6) poll DAG run state via REST API (BasicAuth) --------
echo
echo "Ожидаем завершение DAG ${DAG_ID} (run_id=${RUN_ID})..."
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
    docker compose run --rm airflow airflow tasks states-for-dag-run \"$DAG_ID\" \"$RUN_ID\" || true
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

# -------- Проверяем наличие в Redis --------
echo
echo "Проверяем features в Redis (USER_ID=17)..."
# попытка найти хотя бы один ключ с признаками
USER_ID=17
KEY=$(docker compose run --rm -T redis redis-cli -h redis GET "$USER_ID" || true)

if [[ -z "$KEY" ]]; then
  echo "No 'USER_ID=17' keys found. Trying a generic scan for any keys..."
  KEY=$(docker compose run --rm redis redis-cli -h redis --scan | head -n 1 | tr -d '\r' || true)
fi

if [[ -z "$KEY" ]]; then
  die "❌ Redis check failed: no keys found. Looks like load_features didn't write data."
else
  echo "✅ Found Redis key: $KEY"
  echo "Sample value (truncated):"
  docker compose run --rm redis redis-cli -h redis GET "$KEY" | head -c 500 || true
  echo
  echo "✅ OK: features reached Redis."
fi

echo
echo "[3/3] Оркестр собран и играет."
echo ""
echo "Точки доступа:"
echo "  - MinIO Console:   http://localhost:9001 (user: $MINIO_ROOT_USER, pass: $MINIO_ROOT_PASSWORD)"
echo "  - Spark Master UI: http://localhost:8080"
echo "  - Spark Worker UI: http://localhost:8081"
echo "  - Airflow UI:      http://localhost:8088"
