# Makefile for Multi-Model Multi-Agent System

.PHONY: help install test lint format clean build start stop demo status logs test-models start-bridge stop-bridge restart-bridge start-traefik stop-traefik restart-traefik logs-traefik status-traefik demo-chadgpt chadgpt-models chadgpt-recommend chadgpt-status setup-chadgpt

# Default target
help:
	@echo "🌟 Multi-Model Multi-Agent System"
	@echo "================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run all tests"
	@echo "  test-models - Test with different models"
	@echo "  lint        - Run code linting"
	@echo "  format      - Format code with black"
	@echo "  clean       - Clean temporary files"
	@echo "  build       - Build Docker images"
	@echo "  start       - Start all services (host network)"
	@echo "  start-bridge- Start all services (bridge network)"
	@echo "  start-traefik - Start services with Traefik"
	@echo "  stop        - Stop all services"
	@echo "  restart     - Restart all services"
	@echo "  start-starcoder - Start StarCoder service only"
	@echo "  stop-starcoder  - Stop StarCoder service only"
	@echo "  demo        - Run demo script"
	@echo "  status      - Check service status"
	@echo "  logs        - Show service logs"
	@echo "  logs-traefik  - Show Traefik logs"
	@echo "  health      - Check service health"
	@echo "  stats       - Show service statistics"
	@echo "  full-setup  - Complete system setup (StarCoder + agents)"
	@echo ""
	@echo "🧠 ChadGPT Smart System:"
	@echo "  demo-chadgpt        - Run ChadGPT demo"
	@echo "  chadgpt-models      - Show available ChadGPT models"
	@echo "  chadgpt-recommend   - Get smart model recommendation"
	@echo "  chadgpt-status     - Check ChadGPT configuration"
	@echo "  setup-chadgpt      - Setup ChadGPT with API key"
	@echo ""
	@echo "📦 Poetry Commands:"
	@echo "  poetry-install - Install Poetry dependencies"
	@echo "  poetry-update  - Update Poetry dependencies"
	@echo "  poetry-shell   - Activate Poetry shell"
	@echo "  poetry-add     - Add new dependency"
	@echo "  poetry-add-dev - Add new development dependency"
	@echo "  poetry-export  - Export requirements.txt"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	poetry install

# Run tests
test:
	@echo "🧪 Running tests..."
	poetry run pytest

# Test with different models
test-models:
	@echo "Testing with StarCoder..."
	poetry run python quick_model_test.py starcoder
	@echo "Testing with Mistral..."
	poetry run python quick_model_test.py mistral
	@echo "Testing with Qwen..."
	poetry run python quick_model_test.py qwen
	@echo "Testing with TinyLlama..."
	poetry run python quick_model_test.py tinyllama

# Run linting
lint:
	@echo "🔍 Running linting..."
	poetry run flake8 .
	poetry run mypy .

# Format code
format:
	@echo "🎨 Formatting code..."
	poetry run black .
	poetry run isort .

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache

# Build Docker images
build:
	@echo "🔨 Building Docker images..."
	docker-compose build

# Start all services (host network)
start:
	@echo "🚀 Starting all services..."
	@echo "Checking if StarCoder is running..."
	@if ! docker ps | grep -q starcoder; then \
		echo "Starting StarCoder service..."; \
		docker-compose up -d starcoder; \
	fi
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "Starting agent services..."
	docker-compose up -d generator reviewer

# Start all services (bridge network)
start-bridge:
	@echo "🚀 Starting all services with bridge network..."
	@echo "Checking if StarCoder is running..."
	@if ! docker ps | grep -q starcoder; then \
		echo "Starting StarCoder service..."; \
		docker-compose up -d starcoder; \
	fi
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "Starting agent services..."
	docker-compose up -d generator reviewer

# Start services with Traefik
start-traefik:
	@echo "🚀 Starting services with Traefik..."
	@echo "Checking if local models are built..."
	@docker images | grep local_models || (echo "⚠️  Building local models..."; cd ../local_models && docker-compose build)
	@echo "Starting services..."
	docker-compose -f docker-compose.traefik.yml up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 15
	@echo "🔍 Checking service health..."
	@timeout 60 bash -c 'until curl -f http://generator.localhost/health > /dev/null 2>&1; do echo "Waiting for generator..."; sleep 2; done' || (echo "❌ Generator failed to start"; exit 1)
	@timeout 60 bash -c 'until curl -f http://reviewer.localhost/health > /dev/null 2>&1; do echo "Waiting for reviewer..."; sleep 2; done' || (echo "❌ Reviewer failed to start"; exit 1)
	@echo "✅ All services are running!"
	@echo "🌐 Generator: http://generator.localhost"
	@echo "🌐 Reviewer: http://reviewer.localhost"

# Stop all services
stop:
	@echo "🛑 Stopping all services..."
	docker-compose down

# Restart all services
restart: stop start

# Start StarCoder service only
start-starcoder:
	@echo "🚀 Starting StarCoder service..."
	docker-compose up -d starcoder
	@echo "⏳ Waiting for StarCoder to load..."
	@sleep 30
	@echo "✅ StarCoder is ready!"

# Stop StarCoder service only
stop-starcoder:
	@echo "🛑 Stopping StarCoder service..."
	docker-compose stop starcoder


# Stop bridge network services
stop-bridge:
	@echo "🛑 Stopping bridge network services..."
	docker-compose down

# Restart bridge network services
restart-bridge: stop-bridge start-bridge


# Stop Traefik services
stop-traefik:
	@echo "🛑 Stopping Traefik services..."
	docker-compose -f docker-compose.traefik.yml down

# Restart Traefik services
restart-traefik: stop-traefik start-traefik

# Show service logs
logs:
	@echo "📋 Showing service logs..."
	docker-compose logs -f

# Show Traefik logs
logs-traefik:
	@echo "📋 Showing Traefik logs..."
	docker-compose -f docker-compose.traefik.yml logs -f

# Check service status
status:
	@echo "📊 Service Status:"
	@echo "================="
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check service health
health:
	@echo "🏥 Checking service health..."
	@echo "StarCoder:"
	@curl -s http://localhost:8003/health || echo "❌ StarCoder not responding"
	@echo "Generator:"
	@curl -s http://localhost:9001/health || echo "❌ Generator not responding"
	@echo "Reviewer:"
	@curl -s http://localhost:9002/health || echo "❌ Reviewer not responding"

# Show service statistics
stats:
	@echo "📈 Service Statistics:"
	@echo "====================="
	@docker stats --no-stream

# Run demo
demo:
	@echo "🎭 Running demo..."
	poetry run python demo.py

# Full system setup
full-setup:
	@echo "🛠️  Setting up development environment..."
	@echo "Building StarCoder image..."
	docker-compose build starcoder
	@echo "Starting StarCoder service..."
	docker-compose up -d starcoder
	@echo "Waiting for StarCoder to load..."
	@sleep 30
	@echo "Checking StarCoder health..."
	@timeout 60 bash -c 'until curl -f http://localhost:8003/health; do echo "Waiting for StarCoder..."; sleep 5; done' || (echo "❌ StarCoder failed to start"; exit 1)
	@echo "Starting agent services..."
	docker-compose up -d generator reviewer
	@echo "✅ Full system setup complete!"
	@echo "🌐 StarCoder: http://localhost:8003"
	@echo "🌐 Generator: http://localhost:9001"
	@echo "🌐 Reviewer: http://localhost:9002"

# Quick test
quick-test:
	@echo "⚡ Quick test..."
	poetry run python quick_model_test.py

# Deploy to production
deploy:
	@echo "🚀 Deploying to production..."
	docker-compose -f docker-compose.traefik.yml up -d

# Backup results
backup:
	@echo "💾 Backing up results..."
	tar -czf results_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz results/

# Poetry commands
poetry-install:
	@echo "📦 Installing Poetry dependencies..."
	poetry install

poetry-update:
	@echo "🔄 Updating Poetry dependencies..."
	poetry update

poetry-shell:
	@echo "🐚 Activating Poetry shell..."
	poetry shell

poetry-add:
	@echo "➕ Adding new dependency..."
	@if [ -z "$$PACKAGE" ]; then \
		echo "❌ PACKAGE environment variable is not set"; \
		echo "   Usage: PACKAGE='package-name' make poetry-add"; \
		exit 1; \
	fi
	poetry add $$PACKAGE

poetry-add-dev:
	@echo "➕ Adding new development dependency..."
	@if [ -z "$$PACKAGE" ]; then \
		echo "❌ PACKAGE environment variable is not set"; \
		echo "   Usage: PACKAGE='package-name' make poetry-add-dev"; \
		exit 1; \
	fi
	poetry add --group dev $$PACKAGE

poetry-export:
	@echo "📤 Exporting requirements.txt..."
	poetry export -f requirements.txt --output requirements.txt

# ChadGPT Demo
demo-chadgpt: check-chadgpt-key
	@echo "🌟 Running ChadGPT demo..."
	@echo "=========================="
	poetry run python chadgpt_demo.py

# Check ChadGPT API key
check-chadgpt-key:
	@if [ -z "$$CHADGPT_API_KEY" ]; then \
		echo "❌ CHADGPT_API_KEY is not set"; \
		echo "   Set it with: export CHADGPT_API_KEY='your-key'"; \
		echo "   Or run: make setup-chadgpt"; \
		exit 1; \
	else \
		echo "✅ CHADGPT_API_KEY is set"; \
	fi

# Show available ChadGPT models
chadgpt-models:
	@echo "🤖 Available ChadGPT Models:"
	@echo "============================"
	poetry run python manage_providers.py models

# Get smart model recommendation
chadgpt-recommend:
	@echo "🧠 Smart Model Recommendation:"
	@echo "=============================="
	@if [ -z "$$TASK" ]; then \
		echo "❌ TASK environment variable is not set"; \
		echo "   Usage: TASK='your task description' make chadgpt-recommend"; \
		echo "   Example: TASK='Create a web API' make chadgpt-recommend"; \
		exit 1; \
	fi
	@echo "📝 Task: $$TASK"
	@echo ""
	poetry run python manage_providers.py recommend --task "$$TASK"

# Check ChadGPT status
chadgpt-status:
	@echo "🔍 ChadGPT Configuration Status:"
	@echo "================================"
	@echo "API Key: $$(if [ -n "$$CHADGPT_API_KEY" ]; then echo "✅ Set"; else echo "❌ Not set"; fi)"
	@echo ""
	@echo "Testing ChadGPT connection..."
	poetry run python manage_providers.py test --provider chadgpt-real

# Setup ChadGPT with API key
setup-chadgpt:
	@echo "🔧 Setting up ChadGPT environment..."
	@echo "===================================="
	@if [ -f "../api_key.txt" ]; then \
		echo "📁 Found api_key.txt file"; \
		CHADGPT_KEY=$$(grep "chadgpt" ../api_key.txt | cut -d'=' -f2); \
		if [ -n "$$CHADGPT_KEY" ]; then \
			echo "🔑 Found ChadGPT API key in api_key.txt"; \
			echo "📦 Installing dependencies..."; \
			poetry install; \
			echo "🧪 Testing configuration..."; \
			CHADGPT_API_KEY="$$CHADGPT_KEY" poetry run python manage_providers.py test --provider chadgpt-real; \
			echo ""; \
			echo "✅ Setup complete!"; \
			echo "🔑 To use ChadGPT, run:"; \
			echo "   export CHADGPT_API_KEY=\"$$CHADGPT_KEY\""; \
			echo "   make demo-chadgpt"; \
		else \
			echo "❌ No ChadGPT API key found in api_key.txt"; \
			echo "   Please add: chadgpt=your-api-key"; \
		fi; \
	else \
		echo "❌ api_key.txt file not found"; \
		echo "   Please create ../api_key.txt with: chadgpt=your-api-key"; \
	fi