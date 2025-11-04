#!/usr/bin/env bash
set -Eeuo pipefail

# ===== Конфиг по умолчанию (можно переопределить через env) =====
: "${UI_HOST:=0.0.0.0}"
: "${UI_PORT:=5000}"

: "${SERVE_HOST:=0.0.0.0}"
: "${SERVE_PORT:=6000}"

# ВАЖНО: URI трекинга и реестра должны совпадать
: "${MLFLOW_TRACKING_URI:=http://mlflow:5000}"
: "${MLFLOW_REGISTRY_URI:=${MLFLOW_TRACKING_URI}}"

# Адрес реестра модели, которую надо сервить
: "${SERVE_MODEL_URI:=models:/mlsd_hw3_model/Production}"

# Разрешённые хосты/происхождения для UI (не влияет на порт 6000,
# но оставим корректные значения без «обрезанных» строк)
: "${ALLOWED_HOSTS:=mlflow,mlflow:5000,mlflow:6000,localhost,localhost:5000,localhost:6000,127.0.0.1,127.0.0.1:5000,127.0.0.1:6000}"
: "${CORS_ALLOWED_ORIGINS:=http://localhost:5000,http://127.0.0.1:5000,http://localhost:6000,http://127.0.0.1:6000}"

echo "[entrypoint] TRACKING_URI=${MLFLOW_TRACKING_URI}"
echo "[entrypoint] REGISTRY_URI=${MLFLOW_REGISTRY_URI}"
echo "[entrypoint] MODEL_URI=${SERVE_MODEL_URI}"

# ===== Функции ожидания =====

wait_for_ui() {
  # ходим на loopback и явно подставляем Host, который разрешён
  local url="http://127.0.0.1:${UI_PORT}/"
  echo "[entrypoint] waiting for MLflow UI on :${UI_PORT}..."
  for i in {1..180}; do
    if curl -fsS -H "Host: mlflow:5000" "$url" >/dev/null 2>&1; then
      echo "[entrypoint] UI is up."
      return 0
    fi
    sleep 1
  done
  echo "[entrypoint] UI failed to start in time." >&2
  return 1
}

wait_for_model_available() {
  # ждём ПОЯВЛЕНИЯ версии в нужной стадии в реестре
  local model_uri="${1}"
  local stage name host
  stage="$(sed -n 's#^models:/[^/]\+/\([^/]\+\)$#\1#p' <<<"${model_uri}")"
  name="$(sed -n 's#^models:/\([^/]\+\)/[^/]\+$#\1#p' <<<"${model_uri}")"
  host="$(sed -n 's#^http://##p' <<<"${MLFLOW_REGISTRY_URI}")"
  if [[ -z "${stage}" || -z "${name}" ]]; then
    echo "[entrypoint] Bad SERVE_MODEL_URI='${model_uri}'" >&2
    return 1
  fi

  echo "[entrypoint] waiting for model ${model_uri} to be available..."
  for i in {1..300}; do
    # Сначала проверяем, что эндпоинт жив и отдаёт 200
    local code
    code="$(curl -s -o /dev/null -w '%{http_code}' \
      -X POST "http://${host}/api/2.0/mlflow/registered-models/get-latest-versions" \
      -H 'Content-Type: application/json' \
      --data-raw '{"name":"'"${name}"'","stages":["'"${stage}"'"]}')"

    if [[ "${code}" == "200" ]]; then
      # если 200, уже можно безопасно разбирать ответ jq
      if curl -fsS -X POST "http://${host}/api/2.0/mlflow/registered-models/get-latest-versions" \
          -H 'Content-Type: application/json' \
          --data-raw '{"name":"'"${name}"'","stages":["'"${stage}"'"]}' \
          | jq -e '.model_versions | length >= 1' >/dev/null; then
        echo "[entrypoint] model ${name} in stage ${stage} is available."
        return 0
      fi
    fi
    sleep 2
  done
  echo "[entrypoint] model ${model_uri} is still not available." >&2
  return 1
}

# ===== Старт UI =====
export MLFLOW_TRACKING_URI MLFLOW_REGISTRY_URI

mlflow server \
  --host "${UI_HOST}" \
  --port "${UI_PORT}" \
  --allowed-hosts "${ALLOWED_HOSTS}" \
  --cors-allowed-origins "${CORS_ALLOWED_ORIGINS}" \
  &

ui_pid=$!
trap 'echo "[entrypoint] stopping..."; kill ${ui_pid} ${serve_pid:-} 2>/dev/null || true' EXIT

wait_for_ui

# ===== Ждём модель и запускаем serve с авто-перезапуском =====
wait_for_model_available "${SERVE_MODEL_URI}"

serve_loop() {
  while true; do
    echo "[entrypoint] starting model serve on :${SERVE_PORT}..."
    mlflow models serve \
      -m "${SERVE_MODEL_URI}" \
      -h "${SERVE_HOST}" \
      -p "${SERVE_PORT}" \
      --env-manager local
    rc=$?
    echo "[entrypoint] serve exited with code ${rc}. Restart in 5s..."
    sleep 5
  done
}

serve_loop &
serve_pid=$!

# Держим контейнер живым, если один из процессов упадёт — второй перезапустится/завалит контейнер
wait -n ${ui_pid} ${serve_pid}

