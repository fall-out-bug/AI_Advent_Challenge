# Day 8: Enhanced Token Analysis System
# Makefile for project management

# Default configuration
TOKEN_COUNTER_MODE ?= hybrid
LIMIT_PROFILE ?= practical
AUTO_SWAP_MODELS ?= true

.PHONY: help install install-dev install-ml test test-cov lint format clean build run demo compare-models docker-build docker-run docker-stop docker-logs check setup reset watch-test watch-lint test-zen test-integration docker-restart docker-shell logs-all config-check restart-services

# Default target
help:
	@echo "Day 8: Enhanced Token Analysis System"
	@echo "======================================"
	@echo ""
	@echo "📦 Installation:"
	@echo "  install       Install basic dependencies"
	@echo "  install-dev   Install development dependencies"
	@echo "  install-ml    Install ML dependencies (heavy libraries)"
	@echo "  setup         Full setup (dev + ml + env-example)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test          Run all tests"
	@echo "  test-cov      Run tests with coverage"
	@echo "  test-zen      Run Zen implementation tests"
	@echo "  test-integration Run integration tests"
	@echo "  quick-test    Run tests with short output"
	@echo "  full-test     Run lint + test + test-cov"
	@echo "  check         Quick check (lint + test)"
	@echo ""
	@echo "🎨 Code Quality:"
	@echo "  lint          Run linting (flake8, mypy, pylint, ruff)"
	@echo "  lint-strict   Run strict linting (all linters)"
	@echo "  format        Format code (black, isort)"
	@echo "  security      Run security check (bandit)"
	@echo "  pre-commit    Install pre-commit hooks"
	@echo "  watch-test    Watch files and run tests"
	@echo "  watch-lint    Watch files and run lint"
	@echo ""
	@echo "🚀 Experiments:"
	@echo "  run           Run main experiments"
	@echo "  run-enhanced  Run enhanced experiments with ML service"
	@echo "  demo          Run basic demo script"
	@echo "  demo-switching Run advanced model switching demo with Docker"
	@echo "  demo-quick     Run quick model switching demo (fast, with timeouts)"
	@echo "  demo-working   Run working model switching demo (tests direct connections)"
	@echo "  demo-enhanced  Run comprehensive demo with large queries and all compressions"
	@echo "  compare-models Run model comparison"
	@echo ""
	@echo "🐳 Docker Management:"
	@echo "  docker-build  Build Docker image for ML service"
	@echo "  docker-run    Run ML service in Docker"
	@echo "  docker-stop   Stop ML service"
	@echo "  docker-restart Restart ML service"
	@echo "  docker-shell  Open shell in ML service"
	@echo "  docker-logs   Show Docker logs"
	@echo ""
	@echo "🔧 Service Management:"
	@echo "  start-services Start all services"
	@echo "  stop-services  Stop all services"
	@echo "  restart-services Restart all services"
	@echo "  status         Check service status"
	@echo "  logs-all       Show all relevant logs"
	@echo ""
	@echo "🛠️  Utilities:"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build the project"
	@echo "  reset         Reset to clean state"
	@echo "  config-check  Check current configuration"
	@echo "  env-example   Create .env.example"
	@echo ""
	@echo "⚙️  Configuration:"
	@echo "  TOKEN_COUNTER_MODE=simple|accurate|hybrid"
	@echo "  LIMIT_PROFILE=practical|theoretical"
	@echo "  AUTO_SWAP_MODELS=true|false"
	@echo ""
	@echo "💡 Quick Start:"
	@echo "  make setup && make check && make demo"
	@echo "  make demo-switching  # For advanced Docker-integrated demo"

# Installation targets
install:
	poetry install --only main

install-dev:
	poetry install --with dev

install-ml:
	poetry install --with ml

# Quick workflow targets
check: lint-basic test
	@echo "✅ Quick check completed!"

setup: install-dev install-ml env-example
	@echo "✅ Full setup completed!"
	@echo "Run 'make check' to verify installation"

reset: clean stop-services
	@echo "✅ Reset to clean state completed!"

# Testing targets
test:
	poetry run pytest tests/ -v

test-cov:
	poetry run pytest tests/ --cov=core --cov=utils --cov-report=html --cov-report=term-missing

test-zen:
	@echo "Running Zen implementation tests..."
	poetry run pytest tests/test_zen_implementations.py -v

test-integration:
	@echo "Running integration tests..."
	poetry run pytest tests/ -k "integration" -v

# Code quality targets (basic versions)
lint-basic:
	poetry run flake8 core/ utils/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	poetry run mypy core/ utils/ --ignore-missing-imports

format-basic:
	poetry run black core/ utils/ tests/ --line-length=88
	poetry run isort core/ utils/ tests/ --profile=black --line-length=88

watch-test:
	@echo "Watching for changes and running tests..."
	@if command -v pytest-watch >/dev/null 2>&1; then \
		poetry run pytest-watch tests/ -- -v; \
	else \
		echo "⚠️  pytest-watch not installed. Install with: poetry add --group dev pytest-watch"; \
		echo "Running tests once instead..."; \
		poetry run pytest tests/ -v; \
	fi

watch-lint:
	@echo "Watching for changes and running lint..."
	@if command -v entr >/dev/null 2>&1; then \
		find core/ utils/ tests/ -name "*.py" | entr -c poetry run flake8 core/ utils/ tests/ --max-line-length=88 --extend-ignore=E203,W503; \
	else \
		echo "⚠️  entr not installed. Install with: sudo apt install entr"; \
		echo "Running lint once instead..."; \
		poetry run flake8 core/ utils/ tests/ --max-line-length=88 --extend-ignore=E203,W503; \
	fi

# Build and clean targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	poetry build

# Run targets
run:
	@echo "Running main experiments..."
	@echo "Configuration: TOKEN_COUNTER_MODE=$(TOKEN_COUNTER_MODE), LIMIT_PROFILE=$(LIMIT_PROFILE)"
	@if [ ! -f "main.py" ]; then \
		echo "❌ main.py not found!"; \
		exit 1; \
	fi
	TOKEN_COUNTER_MODE=$(TOKEN_COUNTER_MODE) LIMIT_PROFILE=$(LIMIT_PROFILE) poetry run python main.py

run-enhanced:
	@echo "Running enhanced experiments with ML service..."
	@echo "Configuration: TOKEN_COUNTER_MODE=$(TOKEN_COUNTER_MODE), LIMIT_PROFILE=$(LIMIT_PROFILE)"
	@if [ ! -f "main_enhanced.py" ]; then \
		echo "❌ main_enhanced.py not found!"; \
		exit 1; \
	fi
	@echo "Checking ML service availability..."
	@if ! curl -s http://localhost:8004/health >/dev/null 2>&1; then \
		echo "⚠️  ML service not available, falling back to simple mode"; \
		TOKEN_COUNTER_MODE=simple; \
	fi
	TOKEN_COUNTER_MODE=$(TOKEN_COUNTER_MODE) LIMIT_PROFILE=$(LIMIT_PROFILE) poetry run python main_enhanced.py

demo:
	@echo "Running demo script..."
	@if [ ! -f "demo.py" ]; then \
		echo "❌ demo.py not found!"; \
		exit 1; \
	fi
	poetry run python demo.py

demo-switching:
	@echo "Running advanced model switching demo..."
	@if [ ! -f "demo_model_switching.py" ]; then \
		echo "❌ demo_model_switching.py not found!"; \
		exit 1; \
	fi
	@echo "🚀 Starting Model Switching Demo with Docker Integration"
	@echo "This demo will automatically manage Docker containers"
	poetry run python demo_model_switching.py

demo-quick:
	@echo "Running quick model switching demo..."
	@if [ ! -f "demo_quick.py" ]; then \
		echo "❌ demo_quick.py not found!"; \
		exit 1; \
	fi
	@echo "⚡ Quick Demo - Fast Docker Integration Test"
	@echo "This demo runs quickly with timeouts"
	poetry run python demo_quick.py

demo-working:
	@echo "Running working model switching demo..."
	@if [ ! -f "demo_working.py" ]; then \
		echo "❌ demo_working.py not found!"; \
		exit 1; \
	fi
	@echo "✅ Working Demo - Docker Integration with Direct Testing"
	@echo "This demo tests direct model connections"
	poetry run python demo_working.py

demo-enhanced:
	@echo "Running enhanced comprehensive demo..."
	@if [ ! -f "demo_enhanced.py" ]; then \
		echo "❌ demo_enhanced.py not found!"; \
		exit 1; \
	fi
	@echo "🚀 Enhanced Demo - Comprehensive Testing with Large Queries"
	@echo "This demo tests all models with queries exceeding limits"
	@echo "Tests all compression strategies with detailed output"
	poetry run python demo_enhanced.py

compare-models:
	@echo "Running model comparison..."
	@echo "Configuration: AUTO_SWAP_MODELS=$(AUTO_SWAP_MODELS)"
	@if [ ! -f "compare_models.py" ]; then \
		echo "❌ compare_models.py not found!"; \
		exit 1; \
	fi
	AUTO_SWAP_MODELS=$(AUTO_SWAP_MODELS) poetry run python compare_models.py

# Docker targets for ML service
docker-build:
	@echo "Building Docker image for ML service..."
	@if ! docker info >/dev/null 2>&1; then \
		echo "❌ Docker daemon is not running!"; \
		exit 1; \
	fi
	docker build -t day-08-token-analysis:latest .
	@echo "✅ Docker image built successfully!"

docker-run:
	@echo "Starting ML service in Docker..."
	@if docker ps -q -f name=day-08-token-service | grep -q .; then \
		echo "⚠️  Service already running, stopping first..."; \
		$(MAKE) docker-stop; \
	fi
	docker run -d \
		--name day-08-token-service \
		-p 8004:8004 \
		--restart unless-stopped \
		day-08-token-analysis:latest
	@echo "✅ ML service started! Available at http://localhost:8004"
	@echo "Run 'make docker-logs' to see logs"

docker-stop:
	@echo "Stopping ML service..."
	@docker stop day-08-token-service 2>/dev/null || true
	@docker rm day-08-token-service 2>/dev/null || true
	@echo "✅ ML service stopped and removed"

docker-restart: docker-stop docker-run
	@echo "✅ Docker service restarted!"

docker-shell:
	@echo "Opening shell in ML service container..."
	@if ! docker ps -q -f name=day-08-token-service | grep -q .; then \
		echo "❌ ML service is not running!"; \
		echo "Run 'make docker-run' to start it"; \
		exit 1; \
	fi
	docker exec -it day-08-token-service /bin/bash

docker-logs:
	@if ! docker ps -q -f name=day-08-token-service | grep -q .; then \
		echo "❌ ML service is not running!"; \
		echo "Run 'make docker-run' to start it"; \
		exit 1; \
	fi
	docker logs -f day-08-token-service

# Development workflow targets
dev-setup: install-dev install-ml
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify installation"

full-test: lint-basic test test-cov
	@echo "Full test suite completed!"

# Quick development cycle
quick-test:
	poetry run pytest tests/ -v --tb=short

# Environment setup
env-example:
	@echo "Creating environment configuration example..."
	@echo "# Token Analysis System Configuration" > .env.example
	@echo "TOKEN_COUNTER_MODE=simple" >> .env.example
	@echo "LIMIT_PROFILE=practical" >> .env.example
	@echo "AUTO_SWAP_MODELS=true" >> .env.example
	@echo "MAX_INPUT_TOKENS=4096" >> .env.example
	@echo "MAX_OUTPUT_TOKENS=1024" >> .env.example
	@echo "Environment example created at .env.example"

# Service management
start-services:
	@echo "Starting all services..."
	@echo "1. Building ML service..."
	$(MAKE) docker-build
	@echo "2. Starting ML service..."
	$(MAKE) docker-run
	@echo "3. Services started! ML service available at http://localhost:8004"

stop-services:
	@echo "Stopping all services..."
	$(MAKE) docker-stop
	@echo "All services stopped!"

restart-services: stop-services start-services
	@echo "✅ Services restarted!"

logs-all:
	@echo "Showing all relevant logs..."
	@echo "=== ML Service Logs ==="
	@docker logs --tail=50 day-08-token-service 2>/dev/null || echo "ML service not running"
	@echo ""
	@echo "=== StarCoder Logs ==="
	@docker logs --tail=50 local_models-starcoder-chat-1 2>/dev/null || echo "StarCoder not running"

config-check:
	@echo "Checking configuration..."
	@echo "TOKEN_COUNTER_MODE: $(TOKEN_COUNTER_MODE)"
	@echo "LIMIT_PROFILE: $(LIMIT_PROFILE)"
	@echo "AUTO_SWAP_MODELS: $(AUTO_SWAP_MODELS)"
	@echo ""
	@echo "Poetry environment:"
	@poetry env info --path || echo "No poetry environment found"
	@echo ""
	@echo "Docker services:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(day-08|starcoder)" || echo "No relevant services running"

# Production deployment
deploy: clean build docker-build
	@echo "Deployment ready!"
	@echo "Run 'make start-services' to start production services"

# Monitoring
status:
	@echo "Service Status:"
	@echo "==============="
	@echo "ML Service:"
	@docker ps --filter name=day-08-token-service --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "ML service not running"
	@echo ""
	@echo "StarCoder Service:"
	@docker ps --filter name=starcoder --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "StarCoder not running"
	@echo ""
	@echo "Poetry environment:"
	@poetry env info --path || echo "No poetry environment found"
	@echo ""
	@echo "Configuration:"
	@echo "TOKEN_COUNTER_MODE: $(TOKEN_COUNTER_MODE)"
	@echo "LIMIT_PROFILE: $(LIMIT_PROFILE)"
	@echo "AUTO_SWAP_MODELS: $(AUTO_SWAP_MODELS)"

# Code Quality Commands
lint:
	@echo "Running linting checks..."
	@echo "========================"
	@echo "Running flake8..."
	@poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "Running mypy..."
	@poetry run mypy . --strict
	@echo "Running pylint..."
	@poetry run pylint core/ models/ utils/ --disable=C0114,C0115,C0116,R0903,R0913,W0613
	@echo "Running ruff..."
	@poetry run ruff check . --fix
	@echo "✅ Linting completed!"

lint-strict:
	@echo "Running strict linting checks..."
	@echo "==============================="
	@echo "Running flake8..."
	@poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "Running mypy (strict)..."
	@poetry run mypy . --strict --show-error-codes
	@echo "Running pylint..."
	@poetry run pylint core/ models/ utils/ --disable=C0114,C0115,C0116,R0903,R0913,W0613
	@echo "Running ruff..."
	@poetry run ruff check . --fix
	@echo "Running bandit..."
	@poetry run bandit -r core/ models/ utils/ -f json -o bandit-report.json || true
	@echo "✅ Strict linting completed!"

format:
	@echo "Formatting code..."
	@echo "=================="
	@echo "Running black..."
	@poetry run black . --line-length 88
	@echo "Running isort..."
	@poetry run isort . --profile black
	@echo "Running ruff (format)..."
	@poetry run ruff format .
	@echo "✅ Code formatting completed!"

security:
	@echo "Running security checks..."
	@echo "========================="
	@echo "Running bandit..."
	@poetry run bandit -r core/ models/ utils/ -f json -o bandit-report.json
	@echo "✅ Security check completed!"

pre-commit:
	@echo "Installing pre-commit hooks..."
	@echo "============================="
	@poetry run pre-commit install
	@poetry run pre-commit install --hook-type pre-push
	@echo "✅ Pre-commit hooks installed!"

# Combined quality checks
quality-check: format-basic lint-basic security
	@echo "✅ All quality checks completed!"

full-quality-check: format lint-strict security test-cov
	@echo "✅ Full quality check completed!"
