#!/bin/bash
# Start all local model containers

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LEGACY_DIR="${ROOT_DIR}/archive/legacy/local_models"

if [ ! -d "$LEGACY_DIR" ]; then
    echo "❌ Legacy local model manifests not found at: ${LEGACY_DIR}"
    echo "   Please verify that the repository includes archived assets."
    exit 1
fi

cd "${LEGACY_DIR}" || exit 1
export COMPOSE_PROJECT_NAME=local_models

echo "🚀 Starting local model containers..."
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose not found"
    exit 1
fi

# Use docker compose if available, otherwise docker-compose
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Start Mistral (primary model for code review)
echo "📦 Starting Mistral model (port 8001)..."
$COMPOSE_CMD up -d mistral-chat

echo ""
echo "⏳ Waiting for containers to start..."
sleep 5

echo ""
echo "📊 Container Status:"
$COMPOSE_CMD ps

echo ""
echo "💡 To check model status, run:"
echo "   ./scripts/check_model_status.sh"
echo ""
echo "💡 To wait for model to be ready, run:"
echo "   ./scripts/wait_for_model.sh"
echo ""
echo "💡 To view logs, run:"
echo "   docker logs -f local_models-mistral-chat-1"
