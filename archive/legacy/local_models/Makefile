# Makefile for Local Models Management
# Provides convenient commands for downloading and managing models

.PHONY: help download-all download-model list-models cache-size clean-cache status start stop restart logs

# Default target
help:
	@echo "Local Models Management"
	@echo "======================"
	@echo ""
	@echo "Available commands:"
	@echo "  make download-all     Download all project models"
	@echo "  make download-model   Download specific model (use MODEL=name)"
	@echo "  make list-models      List all project models"
	@echo "  make cache-size       Show current cache size"
	@echo "  make clean-cache      Clean model cache"
	@echo "  make status           Show download status"
	@echo "  make start            Start all chat services"
	@echo "  make stop             Stop all chat services"
	@echo "  make restart          Restart all chat services"
	@echo "  make logs             Show service logs"
	@echo ""
	@echo "Examples:"
	@echo "  make download-all"
	@echo "  make download-model MODEL=Qwen/Qwen1.5-4B-Chat"
	@echo "  make start"
	@echo ""

# Download all models
download-all:
	@echo "🚀 Downloading all project models..."
	./download_models.sh download-all

# Download specific model
download-model:
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Error: MODEL parameter required"; \
		echo "Usage: make download-model MODEL=Qwen/Qwen1.5-4B-Chat"; \
		exit 1; \
	fi
	@echo "📥 Downloading model: $(MODEL)"
	./download_models.sh download-model $(MODEL)

# List all models
list-models:
	@echo "📋 Project models:"
	./download_models.sh list-models

# Show cache size
cache-size:
	@echo "💾 Cache information:"
	./download_models.sh cache-size

# Clean cache
clean-cache:
	@echo "🧹 Cleaning model cache..."
	./download_models.sh clean-cache

# Show status
status:
	@echo "📊 Download status:"
	./download_models.sh status

# Start all services
start:
	@echo "🚀 Starting all chat services..."
	docker-compose up -d

# Stop all services
stop:
	@echo "🛑 Stopping all chat services..."
	docker-compose down

# Restart all services
restart: stop start
	@echo "🔄 Restarted all chat services"

# Show logs
logs:
	@echo "📋 Service logs:"
	docker-compose logs -f

# Build download image
build-download:
	@echo "🔨 Building download image..."
	docker build -f Dockerfile.download -t model-downloader .

# Test services
test:
	@echo "🧪 Testing all services..."
	@echo "Testing Qwen (port 8000)..."
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ Qwen OK" || echo "❌ Qwen Failed"
	@echo "Testing Mistral (port 8001)..."
	@curl -s http://localhost:8001/health > /dev/null && echo "✅ Mistral OK" || echo "❌ Mistral Failed"
	@echo "Testing TinyLlama (port 8002)..."
	@curl -s http://localhost:8002/health > /dev/null && echo "✅ TinyLlama OK" || echo "❌ TinyLlama Failed"
	@echo "Testing StarCoder (port 8003)..."
	@curl -s http://localhost:8003/health > /dev/null && echo "✅ StarCoder OK" || echo "❌ StarCoder Failed"

# Quick setup (download + start)
setup: download-all start
	@echo "🎉 Setup complete! All models downloaded and services started."

# Development mode (start with logs)
dev: start logs
