# 📥 Model Pre-downloading Guide

This guide explains how to pre-download all models used in the AI Challenge project to local cache for faster startup times and offline usage.

## 🎯 Overview

The project uses 4 main models:
- **Qwen/Qwen1.5-4B-Chat** (порт 8000) - быстрые ответы, хорошее качество
- **mistralai/Mistral-7B-Instruct-v0.2** (порт 8001) - высокое качество, рекомендована  
- **TinyLlama/TinyLlama-1.1B-Chat-v1.0** (порт 8002) - компактная, быстрая
- **TechxGenus/starcoder2-7b-instruct** (порт 8003) - для генерации кода

## 🚀 Quick Start

### 1. Set up HuggingFace Token (Optional but Recommended)

Some models require authentication. Set your HuggingFace token:

```bash
# Option 1: Environment variable
export HF_TOKEN="your_huggingface_token_here"

# Option 2: Create .env file
echo "HF_TOKEN=your_huggingface_token_here" > .env
```

### 2. Download All Models

```bash
# Navigate to local_models directory
cd local_models

# Download all models at once
./download_models.sh download-all
```

### 3. Verify Download

```bash
# Check cache size
./download_models.sh cache-size

# List available models
./download_models.sh list-models
```

## 📋 Available Commands

### Basic Commands

```bash
# Download all models
./download_models.sh download-all

# Download specific model
./download_models.sh download-model MODEL_NAME

# List all project models
./download_models.sh list-models

# Check current cache size
./download_models.sh cache-size

# Clean cache (removes all models)
./download_models.sh clean-cache

# Show download status
./download_models.sh status
```

### Examples

```bash
# Download specific models
./download_models.sh download-model Qwen/Qwen1.5-4B-Chat
./download_models.sh download-model mistralai/Mistral-7B-Instruct-v0.2
./download_models.sh download-model TinyLlama/TinyLlama-1.1B-Chat-v1.0
./download_models.sh download-model TechxGenus/starcoder2-7b-instruct

# Check what's downloaded
./download_models.sh status
```

## 🐳 Docker-based Download

The download system uses Docker containers for isolation and consistency:

### Manual Docker Commands

```bash
# Build download image
docker build -f Dockerfile.download -t model-downloader .

# Download all models
docker-compose -f docker-compose.download.yml up model-downloader

# Download specific model
docker run --rm \
  -e HF_TOKEN="${HF_TOKEN:-}" \
  -v hf-model-cache:/home/appuser/.cache/huggingface/hub \
  model-downloader \
  python download_model.py --model "Qwen/Qwen1.5-4B-Chat"
```

### Parallel Downloads

```bash
# Download all models in parallel (faster)
./download_models.sh parallel
```

## 📊 Model Information

| Model | Size | RAM Required | Description |
|-------|------|--------------|-------------|
| **Qwen/Qwen1.5-4B-Chat** | ~8GB | ~8GB | Fast responses, good quality |
| **mistralai/Mistral-7B-Instruct-v0.2** | ~14GB | ~14GB | High quality, recommended |
| **TinyLlama/TinyLlama-1.1B-Chat-v1.0** | ~2GB | ~4GB | Compact, fast |
| **TechxGenus/starcoder2-7b-instruct** | ~14GB | ~14GB | Code generation |

**Total cache size**: ~38GB for all models

## 🔧 Advanced Usage

### Custom Cache Directory

```bash
# Use custom cache directory
docker run --rm \
  -e HF_TOKEN="${HF_TOKEN:-}" \
  -v /path/to/custom/cache:/home/appuser/.cache/huggingface/hub \
  model-downloader \
  python download_model.py --all --cache-dir /home/appuser/.cache/huggingface/hub
```

### Python Script Direct Usage

```bash
# Run download script directly
python download_model.py --all
python download_model.py --model "Qwen/Qwen1.5-4B-Chat"
python download_model.py --list
python download_model.py --cache-size
```

## 🚨 Troubleshooting

### Authentication Issues

```bash
# Check if HF_TOKEN is set
echo $HF_TOKEN

# Set token if missing
export HF_TOKEN="your_token_here"
```

### Disk Space Issues

```bash
# Check available space
df -h

# Clean cache if needed
./download_models.sh clean-cache
```

### Network Issues

```bash
# Test connectivity
curl -I https://huggingface.co

# Use proxy if needed
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"
```

### Docker Issues

```bash
# Check Docker status
docker --version
docker-compose --version

# Clean Docker cache
docker system prune -a
```

## 📈 Performance Tips

### 1. Use Parallel Downloads
```bash
./download_models.sh parallel
```

### 2. Download During Off-Peak Hours
Models are large, so download during low-usage periods.

### 3. Use SSD Storage
Place cache on SSD for faster I/O.

### 4. Monitor Progress
```bash
# Watch download progress
docker-compose -f docker-compose.download.yml logs -f
```

## 🔄 Integration with Chat Services

Once models are downloaded, they will be automatically used by the chat services:

```bash
# Start chat services (will use cached models)
docker-compose up -d

# Verify services are running
curl http://localhost:8000/health  # Qwen
curl http://localhost:8001/health  # Mistral
curl http://localhost:8002/health  # TinyLlama
curl http://localhost:8003/health  # StarCoder
```

## 📝 File Structure

```
local_models/
├── download_model.py              # Main download script
├── download_models.sh            # Management script
├── Dockerfile.download           # Docker image for downloading
├── docker-compose.download.yml   # Docker Compose for downloads
├── requirements.download.txt     # Minimal dependencies
└── README.md                     # This file
```

## 🎉 Success Indicators

You'll know the download was successful when:

1. **Cache size increases**: `./download_models.sh cache-size` shows > 0
2. **No errors in logs**: Download completes without errors
3. **Services start faster**: Chat services load models from cache
4. **Offline usage works**: Models work without internet connection

## 🔗 Related Documentation

- [Local Models README](README.md) - Main local models documentation
- [Docker Compose Guide](docker-compose.yml) - Chat services configuration
- [API Documentation](../day_07/docs/) - Multi-agent system documentation

---

**💡 Tip**: Pre-downloading models significantly improves startup times and enables offline usage. It's especially useful for development and production deployments.
