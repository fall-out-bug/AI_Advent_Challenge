#!/usr/bin/env bash
# Helper script to start shared infrastructure stack required by integration tests.
# Loads environment variables from ~/work/infra/.env.infra and runs `make day-12-up`
# inside the shared infra repository. Override INFRA_DIR if your infra repo lives elsewhere.

set -euo pipefail

INFRA_DIR=${INFRA_DIR:-"$HOME/work/infra"}
ENV_FILE="$INFRA_DIR/.env.infra"

if [ ! -d "$INFRA_DIR" ]; then
  echo "Shared infra repository not found at $INFRA_DIR. Set INFRA_DIR to the correct path." >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file $ENV_FILE is missing. Ensure shared infra repo is bootstrapped." >&2
  exit 1
fi

# Load environment variables without clobbering existing ones unless absent.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

SCRIPT="$INFRA_DIR/scripts/start-infra.sh"
if [ ! -x "$SCRIPT" ]; then
  echo "Start script not found or not executable: $SCRIPT" >&2
  exit 1
fi

echo "Starting shared infrastructure via $SCRIPT"
"$SCRIPT" "$@"
