.PHONY: help install test lint format clean docker-build docker-up docker-down coverage integration e2e maintenance-cleanup maintenance-backup maintenance-export maintenance-validate day-07 day-08 day-11 day-11-up day-11-down day-11-build day-11-logs day-11-logs-bot day-11-logs-worker day-11-logs-mcp day-11-logs-mistral day-11-ps day-11-restart day-11-clean day-11-setup day-12 day-12-up day-12-down day-12-build day-12-logs day-12-logs-bot day-12-logs-worker day-12-logs-mcp day-12-logs-post-fetcher day-12-logs-mistral day-12-ps day-12-restart day-12-clean day-12-setup day-12-test day-12-metrics mcp-discover mcp-demo test-mcp test-mcp-comprehensive mcp-chat mcp-chat-streaming mcp-server-start mcp-server-stop mcp-chat-docker mcp-demo-start mcp-demo-stop mcp-demo-logs demo-mcp-comprehensive

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make unit             - Run unit tests only"
	@echo "  make integration      - Run integration tests"
	@echo "  make e2e              - Run E2E tests"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make lint              - Run linters"
	@echo "  make format           - Format code"
	@echo "  make clean             - Clean temporary files"
	@echo "  make docker-build      - Build Docker image"
	@echo "  make docker-up        - Start Docker services"
	@echo "  make docker-down      - Stop Docker services"
	@echo ""
	@echo "Day 11 - Butler Bot:"
	@echo "  make day-11           - Start Day 11 Butler Bot system (default)"
	@echo "  make day-11-up         - Start all Day 11 services"
	@echo "  make day-11-down       - Stop all Day 11 services"
	@echo "  make day-11-build      - Rebuild Day 11 Docker images"
	@echo "  make day-11-logs       - View logs from all services"
	@echo "  make day-11-logs-bot   - View bot logs"
	@echo "  make day-11-logs-worker - View worker logs"
	@echo "  make day-11-logs-mcp   - View MCP server logs"
	@echo "  make day-11-logs-mistral - View Mistral LLM logs"
	@echo "  make day-11-ps         - Show service status"
	@echo "  make day-11-restart    - Restart all services"
	@echo "  make day-11-clean      - Remove all containers and volumes"
	@echo "  make day-11-setup      - Create .env from .env.example"
	@echo ""
	@echo "Day 12 - Butler Bot with Post Fetcher & PDF Digest:"
	@echo "  make day-12           - Start Day 12 Butler Bot system (default)"
	@echo "  make day-12-up         - Start all Day 12 services"
	@echo "  make day-12-down       - Stop all Day 12 services"
	@echo "  make day-12-build      - Rebuild Day 12 Docker images"
	@echo "  make day-12-logs       - View logs from all services"
	@echo "  make day-12-logs-bot   - View bot logs"
	@echo "  make day-12-logs-worker - View summary worker logs"
	@echo "  make day-12-logs-post-fetcher - View post fetcher worker logs"
	@echo "  make day-12-logs-mcp   - View MCP server logs"
	@echo "  make day-12-logs-mistral - View Mistral LLM logs"
	@echo "  make day-12-ps         - Show service status"
	@echo "  make day-12-restart    - Restart all services"
	@echo "  make day-12-clean      - Remove all containers and volumes"
	@echo "  make day-12-setup      - Create .env from .env.example"
	@echo "  make day-12-test       - Run Day 12 tests"
	@echo "  make day-12-metrics    - View Prometheus metrics"
	@echo ""
	@echo "  make day-07           - Run Day 07 multi-agent workflow"
	@echo "  make day-08           - Run Day 08 token compression"
	@echo "  make mcp-discover     - Discover MCP tools"
	@echo "  make mcp-demo         - Run Day 09 MCP demo"
	@echo "  make test-mcp         - Run MCP tests"
	@echo "  make test-mcp-comprehensive - Run comprehensive MCP integration tests"
	@echo "  make mcp-chat         - Run interactive Mistral chat (Phase 4, stdio)"
	@echo "  make mcp-chat-streaming - Run streaming Mistral chat (Phase 4, stdio)"
	@echo "  make mcp-chat-docker  - Run streaming Mistral chat with Docker MCP server"
	@echo "  make demo-mcp-comprehensive - Run comprehensive MCP demo (all tools and chains)"
	@echo "  make mcp-server-start - Start MCP HTTP server in Docker"
	@echo "  make mcp-server-stop  - Stop MCP HTTP server in Docker"
	@echo "  make mcp-demo-start - Start minimal MCP demo (Mistral + StarCoder + MCP)"
	@echo "  make mcp-demo-stop - Stop MCP demo services"
	@echo "  make maintenance-cleanup - Clean up old data"
	@echo "  make maintenance-backup - Create backup"
	@echo "  make maintenance-export - Export data"
	@echo "  make maintenance-validate - Validate system"

install:
	poetry install

test:
	poetry run pytest tests/ -v

test-unit:
	poetry run pytest tests/unit/ -v

test-integration:
	poetry run pytest tests/integration/ -v

test-e2e:
	poetry run pytest tests/e2e/ -v -m e2e

test-coverage:
	poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80

test-all:
	poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml --cov-fail-under=80

# Legacy aliases for backward compatibility
unit: test-unit
integration: test-integration
e2e: test-e2e
coverage: test-coverage

lint:
	poetry run flake8 src
	poetry run mypy src
	poetry run bandit -r src

format:
	poetry run black src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .pytest_cache/ .mypy_cache/

docker-build:
	docker build -t ai-challenge:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

maintenance-cleanup:
	poetry run python -m scripts.maintenance.cleanup

maintenance-backup:
	poetry run python -m scripts.maintenance.backup

maintenance-export:
	poetry run python -m scripts.maintenance.export_data

maintenance-validate:
	poetry run python -m scripts.maintenance.validate

day-07:
	poetry run python scripts/day_07_workflow.py

day-08:
	poetry run python scripts/day_08_compression.py

mcp-discover:
	poetry run python examples/mcp/basic_discovery.py

mcp-demo:
	poetry run python scripts/day_09_mcp_demo_report.py

test-mcp:
	poetry run pytest src/tests/presentation/mcp -v

test-mcp-comprehensive:
	@echo "Running comprehensive MCP integration tests..."
	poetry run pytest tests/integration/test_mcp_comprehensive_demo.py -v

mcp-chat:
	poetry run python src/presentation/mcp/cli/interactive_mistral_chat.py

mcp-chat-streaming:
	poetry run python src/presentation/mcp/cli/streaming_chat.py

mcp-chat-docker:
	@echo "Starting chat with Docker MCP server..."
	@echo "Make sure MCP server is running: make mcp-server-start"
	MCP_USE_DOCKER=true poetry run python src/presentation/mcp/cli/streaming_chat.py

demo-mcp-comprehensive:
	@echo "Running comprehensive MCP demo..."
	@echo "Make sure MCP server is running: make mcp-server-start"
	poetry run python scripts/mcp_comprehensive_demo.py

mcp-server-start:
	docker-compose -f docker-compose.mcp-demo.yml up -d
	@echo "MCP server starting on http://localhost:8004"
	@echo "Check logs: docker logs mcp-server-day10"

mcp-server-stop:
	docker-compose -f docker-compose.mcp-demo.yml down

mcp-demo-start:
	docker-compose -f docker-compose.mcp-demo.yml up -d
	@echo "MCP demo starting: Mistral + StarCoder + MCP Server"
	@echo "Check logs: make mcp-demo-logs"

mcp-demo-stop:
	docker-compose -f docker-compose.mcp-demo.yml down

mcp-demo-logs:
	docker-compose -f docker-compose.mcp-demo.yml logs -f

# Day 11: 24/7 Personal Butler Telegram Bot
day-11: day-11-up
	@echo "Day 11 Butler Bot system started"
	@echo "Check status: make day-11-ps"
	@echo "View logs: make day-11-logs"

day-11-up:
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found!"; \
		echo "Copy .env.example to .env and set TELEGRAM_BOT_TOKEN"; \
		exit 1; \
	fi
	@if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep -q "TELEGRAM_BOT_TOKEN=your_bot_token_here" .env || grep -q "^TELEGRAM_BOT_TOKEN=$$" .env; then \
		echo "ERROR: TELEGRAM_BOT_TOKEN not set in .env file!"; \
		echo "Edit .env and set your Telegram bot token"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.day11.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker-compose -f docker-compose.day11.yml ps

day-11-down:
	docker-compose -f docker-compose.day11.yml down

day-11-build:
	docker-compose -f docker-compose.day11.yml build --no-cache

day-11-logs:
	docker-compose -f docker-compose.day11.yml logs -f

day-11-logs-bot:
	docker-compose -f docker-compose.day11.yml logs -f telegram-bot

day-11-logs-worker:
	docker-compose -f docker-compose.day11.yml logs -f summary-worker

day-11-logs-mcp:
	docker-compose -f docker-compose.day11.yml logs -f mcp-server

day-11-logs-mistral:
	docker-compose -f docker-compose.day11.yml logs -f mistral-chat

day-11-ps:
	docker-compose -f docker-compose.day11.yml ps

day-11-restart:
	docker-compose -f docker-compose.day11.yml restart

day-11-clean:
	docker-compose -f docker-compose.day11.yml down -v
	@echo "All Day 11 containers and volumes removed"

day-11-setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env and set TELEGRAM_BOT_TOKEN"; \
	else \
		echo ".env file already exists"; \
	fi

# Day 12: Post Fetcher Worker & PDF Digest Generation
day-12: day-12-up
	@echo "Day 12 Butler Bot system started"
	@echo "Check status: make day-12-ps"
	@echo "View logs: make day-12-logs"
	@echo "View metrics: make day-12-metrics"

day-12-up:
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found!"; \
		echo "Copy .env.example to .env and set TELEGRAM_BOT_TOKEN"; \
		exit 1; \
	fi
	@if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep -q "TELEGRAM_BOT_TOKEN=your_bot_token_here" .env || grep -q "^TELEGRAM_BOT_TOKEN=$$" .env; then \
		echo "ERROR: TELEGRAM_BOT_TOKEN not set in .env file!"; \
		echo "Edit .env and set your Telegram bot token"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.day12.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker-compose -f docker-compose.day12.yml ps

day-12-down:
	docker-compose -f docker-compose.day12.yml down

day-12-build:
	docker-compose -f docker-compose.day12.yml build --no-cache

day-12-logs:
	docker-compose -f docker-compose.day12.yml logs -f

day-12-logs-bot:
	docker-compose -f docker-compose.day12.yml logs -f telegram-bot

day-12-logs-worker:
	docker-compose -f docker-compose.day12.yml logs -f summary-worker

day-12-logs-post-fetcher:
	docker-compose -f docker-compose.day12.yml logs -f post-fetcher-worker

day-12-logs-mcp:
	docker-compose -f docker-compose.day12.yml logs -f mcp-server

day-12-logs-mistral:
	docker-compose -f docker-compose.day12.yml logs -f mistral-chat

day-12-ps:
	docker-compose -f docker-compose.day12.yml ps

day-12-restart:
	docker-compose -f docker-compose.day12.yml restart

day-12-clean:
	docker-compose -f docker-compose.day12.yml down -v
	@echo "All Day 12 containers and volumes removed"

day-12-setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env and set:"; \
		echo "  - TELEGRAM_BOT_TOKEN"; \
		echo "  - TELEGRAM_API_ID (optional, for Pyrogram)"; \
		echo "  - TELEGRAM_API_HASH (optional, for Pyrogram)"; \
		echo "  - TELEGRAM_SESSION_STRING (optional, for Pyrogram)"; \
	else \
		echo ".env file already exists"; \
	fi

day-12-test:
	@echo "Running Day 12 tests..."
	python scripts/day12_run.py test

day-12-metrics:
	@echo "Fetching Prometheus metrics from MCP server..."
	@curl -s http://localhost:8004/metrics | grep -E "(post_fetcher|pdf_generation|bot_digest)" | head -20 || echo "Metrics endpoint not available. Make sure services are running: make day-12-up"
