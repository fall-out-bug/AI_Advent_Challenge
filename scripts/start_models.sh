#!/bin/bash
# Start all local model containers

set -e

cd "$(dirname "$0")/../local_models" || exit 1

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

