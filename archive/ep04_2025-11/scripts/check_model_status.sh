#!/bin/bash
# Check status of local models

echo "🔍 Checking local model status..."
echo ""

# Check Mistral
echo "Mistral (Port 8001):"
if docker ps --filter "name=local_models-mistral-chat" \
    --format "{{.Status}}" | grep -q "Up"; then
    echo "  ✅ Container is running"

    # Check health endpoint
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "  ✅ Health endpoint responds"

        # Try a test request
        response=$(curl -s -X POST http://localhost:8001/v1/chat/completions \
            -H "Content-Type: application/json" \
            -d '{"model":"mistral","messages":[{"role":"user","content":"test"}],"max_tokens":10}' 2>&1)

        if echo "$response" | grep -q "choices\|error"; then
            echo "  ✅ Model API is working"
        else
            echo "  ⚠️  Model API may not be ready yet"
            echo "     Response: ${response:0:100}"
        fi
    else
        echo "  ⏳ Health endpoint not ready (model may still be loading)"
    fi
else
    echo "  ❌ Container is not running"
    echo "     Start with: cd archive/legacy/local_models && docker-compose up -d mistral-chat"
fi

echo ""
echo "📊 Container Details:"
docker ps --filter "name=local_models-mistral-chat" \
    --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
