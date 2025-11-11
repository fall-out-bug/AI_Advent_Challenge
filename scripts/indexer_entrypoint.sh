#!/usr/bin/env bash

set -euo pipefail

WORKDIR="${WORKDIR:-/workspace}"
INDEX_RUN_ARGS="${INDEX_RUN_ARGS:-}"

cd "${WORKDIR}"

INFRA_ENV_FILE="${INFRA_ENV_FILE:-/root/work/infra/.env.infra}"
if [[ -f "${INFRA_ENV_FILE}" ]]; then
  echo "[indexer] Loading infra environment from ${INFRA_ENV_FILE}"
  # shellcheck disable=SC1090
  set -a
  source "${INFRA_ENV_FILE}"
  set +a
fi

command=(poetry run python -m src.presentation.cli.backoffice.main index run)
if [[ -n "${INDEX_RUN_ARGS}" ]]; then
  # shellcheck disable=SC2206
  extra_args=(${INDEX_RUN_ARGS})
  command+=("${extra_args[@]}")
fi

command_string="$(printf '%s ' "${command[@]}")"
command_string="${command_string% }"

if [[ "${CHECK_ONLY:-0}" == "1" ]]; then
  echo "${command_string}"
  exit 0
fi

if [[ "${SKIP_POETRY_INSTALL:-0}" != "1" ]]; then
  echo "[indexer] Installing dependencies via Poetry..."
  poetry install --no-interaction --no-ansi
fi

echo "[indexer] Running: ${command_string}"
exec "${command[@]}"
