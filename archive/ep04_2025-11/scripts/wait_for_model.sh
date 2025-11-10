#!/bin/bash
# Wait for Mistral model to be ready

echo "Waiting for Mistral model to be ready..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Mistral model is ready!"
        exit 0
    fi

    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - waiting 10 seconds..."
    sleep 10
done

echo "❌ Model did not become ready after ${max_attempts} attempts"
exit 1
