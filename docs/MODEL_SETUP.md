# Local Model Setup Guide

## Quick Start

### 1. Start Mistral Container

```bash
cd local_models
docker-compose up -d mistral-chat
```

### 2. Wait for Model to Load

First time: Model downloads and loads (5-10 minutes)
Subsequent: Container starts quickly (~30 seconds)

Check status:
```bash
# Check container
docker ps | grep mistral

# Check health endpoint
curl http://localhost:8001/health

# Check logs
docker logs local_models-mistral-chat-1
```

### 3. Verify Model Works

```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

## Configuration

### Model Endpoint

The model runs on `http://localhost:8001` (port 8001).

Configuration is in `shared/shared_package/config/models.py`:

```python
ModelName.MISTRAL.value: {
    "type": ModelType.LOCAL.value,
    "port": ModelPort.MISTRAL.value,  # 8001
    "url": f"http://localhost:{ModelPort.MISTRAL.value}",
    "openai_compatible": True
}
```

### UnifiedModelClient Usage

```python
from shared_package.clients.unified_client import UnifiedModelClient

client = UnifiedModelClient(timeout=300.0)
response = await client.make_request(
    model_name="mistral",
    prompt="Review this code...",
    max_tokens=1000,
    temperature=0.7
)
```

## Troubleshooting

### Container Not Starting

```bash
# Check logs
docker logs local_models-mistral-chat-1

# Common issues:
# - GPU not available (remove runtime: nvidia from docker-compose.yml)
# - Port 8001 already in use (change port mapping)
# - Out of memory (reduce model size or add swap)
```

### Model Not Responding

```bash
# Check if container is running
docker ps | grep mistral

# Check health
curl http://localhost:8001/health

# Restart container
docker-compose restart mistral-chat
```

### Connection Errors

If `UnifiedModelClient` can't connect:

1. Verify endpoint: `http://localhost:8001`
2. Check firewall/network settings
3. Verify model is loaded (check logs for "Model loaded")
4. Try increasing timeout: `UnifiedModelClient(timeout=600.0)`

## Resources

- **Memory**: ~14GB RAM required for Mistral-7B
- **GPU**: NVIDIA GPU recommended (CUDA)
- **Storage**: ~15GB for model cache
- **Port**: 8001 (configurable)

## Alternative: Use Different Model

Change `model_name` parameter:

- `"qwen"` - Port 8000 (Qwen-4B, faster)
- `"mistral"` - Port 8001 (Mistral-7B, recommended)
- `"tinyllama"` - Port 8002 (TinyLlama-1.1B, smaller)

Start corresponding container:
```bash
docker-compose up -d qwen-chat    # Port 8000
docker-compose up -d mistral-chat # Port 8001
docker-compose up -d tinyllama-chat # Port 8002
```

