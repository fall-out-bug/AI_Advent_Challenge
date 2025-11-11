.PHONY: help install test lint format clean docker-build docker-up docker-down coverage integration e2e maintenance-cleanup maintenance-backup maintenance-export maintenance-validate day-07 day-08 day-11 day-11-up day-11-down day-11-build day-11-logs day-11-logs-bot day-11-logs-worker day-11-logs-mcp day-11-ps day-11-restart day-11-clean day-11-setup day-12 day-12-up day-12-down day-12-build day-12-logs day-12-logs-bot day-12-logs-worker day-12-logs-post-fetcher day-12-logs-mcp day-12-ps day-12-restart day-12-clean day-12-setup day-12-test day-12-metrics butler butler-up butler-down butler-build butler-logs butler-logs-bot butler-logs-worker butler-logs-mcp butler-logs-post-fetcher butler-ps butler-restart butler-clean butler-setup butler-test butler-metrics mcp-discover mcp-demo test-mcp test-mcp-comprehensive mcp-chat mcp-chat-streaming mcp-server-start mcp-server-stop mcp-chat-docker mcp-demo-start mcp-demo-stop mcp-demo-logs demo-mcp-comprehensive index-run index-container-build index-container-run index-container-shell

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
	@echo "Code Quality & Security:"
	@echo "  make check-all        - Run all checks (format, lint, test, coverage, security)"
	@echo "  make security          - Run security checks (bandit, safety)"
	@echo "  make update-deps      - Check for outdated dependencies"
	@echo "  make docs-check       - Check markdown links"
	@echo ""
	@echo "Pre-commit Hooks:"
	@echo "  make hook             - Install pre-commit hooks"
	@echo "  make hook-update      - Update pre-commit hooks"
	@echo "  make hook-run         - Run pre-commit hooks on all files"
	@echo "  make hook-run-full    - Run manual-stage hooks on all files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-clean     - Clean unused Docker images and containers"
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
	@echo "  make day-11-ps         - Show service status"
	@echo "  make day-11-restart    - Restart all services"
	@echo "  make day-11-clean      - Remove all containers and volumes"
	@echo "  make day-11-setup      - Create .env from .env.example"
	@echo ""
	@echo "Butler - Butler Bot with Post Fetcher & PDF Digest:"
	@echo "  make butler           - Start Butler Bot system (unified, default)"
	@echo "  make butler-up         - Start all Butler services"
	@echo "  make butler-down       - Stop all Butler services"
	@echo "  make butler-build      - Rebuild Butler Docker images"
	@echo "  make butler-logs       - View logs from all services"
	@echo "  make butler-logs-bot   - View bot logs"
	@echo "  make butler-logs-worker - View unified task worker logs"
	@echo "  make butler-logs-post-fetcher - View post fetcher worker logs"
	@echo "  make butler-logs-mcp   - View MCP server logs"
	@echo "  make butler-ps         - Show service status"
	@echo "  make butler-restart    - Restart all services"
	@echo "  make butler-clean      - Remove all containers and volumes"
	@echo "  make butler-setup      - Create .env from .env.example"
	@echo "  make butler-test       - Run Butler tests"
	@echo "  make butler-metrics    - View Prometheus metrics"
	@echo ""
	@echo "Day 17 - Code Review Queue & API:"
	@echo "  make review-worker     - Start review worker (processes review tasks)"
	@echo "  make review-test       - Run review system unit tests"
	@echo "  make review-e2e        - Run review E2E tests with real ZIP archives"
	@echo "  make review-health-check - Run comprehensive health check (all components)"
	@echo ""
	@echo "  (Legacy: make butler-* still works but deprecated, use butler-* instead)"
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
	@echo "  make index-run         - Execute Stage 19 document embedding index pipeline"
	@echo "  make index-container-build - Build embedding index container image"
	@echo "  make index-container-run   - Run embedding index pipeline inside container"
	@echo "  make index-container-shell - Open shell inside embedding index container"

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
	poetry run mypy src --ignore-missing-imports
	poetry run mypy packages/multipass-reviewer/multipass_reviewer --strict
	poetry run bandit -r src

lint-allowlist:
	poetry run flake8 --config packages/multipass-reviewer/.flake8 packages/multipass-reviewer/multipass_reviewer
	poetry run flake8 --config shared/.flake8 shared/shared_package/agents shared/shared_package/clients
	poetry run flake8 --max-line-length=120 src/application/services/modular_review_service.py src/application/use_cases/review_submission_use_case.py
	poetry run mypy shared/shared_package/agents shared/shared_package/clients
	poetry run mypy packages/multipass-reviewer/multipass_reviewer
	poetry run mypy --ignore-missing-imports src/application/services/modular_review_service.py src/application/use_cases/review_submission_use_case.py

lint-debt:
	poetry run flake8 --count --exit-zero src tests shared packages

dev:
	docker compose -f docker-compose.dev.yml run --rm dev

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

backoffice-cli:
	poetry run python -m src.presentation.cli.backoffice.main --help

backoffice-digest-help:
	poetry run python -m src.presentation.cli.backoffice.main digest --help

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

index-run:
	poetry run python -m src.presentation.cli.backoffice.main index run

INDEX_COMPOSE_FILE := docker-compose.indexer.yml

index-container-build:
	docker compose -f $(INDEX_COMPOSE_FILE) build embedding-indexer

index-container-run:
	docker compose -f $(INDEX_COMPOSE_FILE) run --rm embedding-indexer

index-container-shell:
	docker compose -f $(INDEX_COMPOSE_FILE) run --rm embedding-indexer bash

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
	docker compose -f archive/docker-compose/docker-compose.day11.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker compose -f archive/docker-compose/docker-compose.day11.yml ps

day-11-down:
	docker compose -f archive/docker-compose/docker-compose.day11.yml down

day-11-build:
	docker compose -f archive/docker-compose/docker-compose.day11.yml build --no-cache

day-11-logs:
	docker compose -f archive/docker-compose/docker-compose.day11.yml logs -f

day-11-logs-bot:
	docker compose -f archive/docker-compose/docker-compose.day11.yml logs -f telegram-bot

day-11-logs-worker:
	docker compose -f archive/docker-compose/docker-compose.day11.yml logs -f summary-worker

day-11-logs-mcp:
	docker compose -f archive/docker-compose/docker-compose.day11.yml logs -f mcp-server

day-11-ps:
	docker compose -f archive/docker-compose/docker-compose.day11.yml ps

day-11-restart:
	docker compose -f archive/docker-compose/docker-compose.day11.yml restart

	docker compose -f archive/docker-compose/docker-compose.day11.yml down -v
	@echo "All Day 11 containers and volumes removed"

day-11-setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env and set TELEGRAM_BOT_TOKEN"; \
	else \
		echo ".env file already exists"; \
	fi

butler: butler-up

butler-up:
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
	docker-compose -f docker-compose.butler.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@docker-compose -f docker-compose.butler.yml ps
	@echo "Butler Bot system started"
	@echo "Check status: make butler-ps"
	@echo "View logs: make butler-logs"
	@echo "View metrics: make butler-metrics"

day-12: butler  # Legacy alias
day-12-up: butler-up  # Legacy alias

day-12-down: butler-down  # Legacy alias
butler-down:
	docker-compose -f docker-compose.butler.yml down

day-12-build: butler-build  # Legacy alias
butler-build:
	docker-compose -f docker-compose.butler.yml build --no-cache

# Legacy aliases for day-12 commands
day-12-logs: butler-logs
day-12-logs-bot: butler-logs-bot
day-12-logs-worker: butler-logs-worker
day-12-logs-post-fetcher: butler-logs-post-fetcher
day-12-logs-mcp: butler-logs-mcp
day-12-ps: butler-ps
day-12-restart: butler-restart
day-12-clean: butler-clean
day-12-setup: butler-setup
day-12-test: butler-test
day-12-metrics: butler-metrics

butler-logs:
	docker-compose -f docker-compose.butler.yml logs -f

butler-logs-bot:
	docker-compose -f docker-compose.butler.yml logs -f butler-bot

butler-logs-worker:
	docker-compose -f docker-compose.butler.yml logs -f unified-task-worker

butler-logs-post-fetcher:
	docker-compose -f docker-compose.butler.yml logs -f post-fetcher-worker

butler-logs-mcp:
	docker-compose -f docker-compose.butler.yml logs -f mcp-server

butler-ps:
	docker-compose -f docker-compose.butler.yml ps

butler-restart:
	docker-compose -f docker-compose.butler.yml restart

butler-clean:
	docker-compose -f docker-compose.butler.yml down -v
	@echo "All Butler containers and volumes removed"

butler-setup:
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

butler-test:
	@echo "Running Butler integration tests..."
	poetry run pytest tests/integration/butler -q

butler-metrics:
	@echo "Fetching Prometheus metrics from MCP server..."
	@curl -s http://localhost:8004/metrics | grep -E "(post_fetcher|pdf_generation|bot_digest|long_tasks)" | head -30 || echo "Metrics endpoint not available. Make sure services are running: make butler-up"

# Code quality and security checks
check-all: format lint test-coverage security
	@echo "All checks completed successfully"

security:
	@echo "Running security checks..."
	poetry run bandit -r src/ -ll
	poetry run safety check --json || echo "Safety check completed (may show warnings)"

update-deps:
	@echo "Checking for outdated dependencies..."
	poetry update --dry-run

docker-clean:
	@echo "Cleaning unused Docker images and containers..."
	docker system prune -f
	docker image prune -f

docs-check:
	@echo "Checking markdown links..."
	@command -v markdown-link-check >/dev/null && find . -name "*.md" -not -path "./.venv/*" -not -path "./node_modules/*" -exec markdown-link-check {} \; || echo "markdown-link-check not installed, skipping"

repo-cleanup-dry-run:
	poetry run python -m tools.repo_cleanup --config docs/specs/epic_06/repo_cleanup_plan.json --base-dir $(PWD)

repo-cleanup-apply:
	poetry run python -m tools.repo_cleanup --config docs/specs/epic_06/repo_cleanup_plan.json --base-dir $(PWD) --execute

repo-cleanup-apply-git:
	poetry run python -m tools.repo_cleanup --config docs/specs/epic_06/repo_cleanup_plan.json --base-dir $(PWD) --execute --use-git

# Pre-commit hooks
hook:
	@echo "Installing pre-commit hooks..."
	poetry run pre-commit install

hook-update:
	@echo "Updating pre-commit hooks..."
	poetry run pre-commit autoupdate

hook-run:
	@echo "Running pre-commit hooks on all files..."
	poetry run pre-commit run --all-files

hook-run-full:
	@echo "Running manual-stage pre-commit hooks on all files..."
	poetry run pre-commit run --hook-stage manual --all-files

# Day 17: Code Review Queue & API
review-worker:
	@echo "Note: Review tasks are now processed by unified-task-worker"
	@echo "Use: make unified-task-worker or docker-compose up unified-task-worker"

unified-task-worker:
	@echo "Starting unified task worker (summarization + review)..."
	poetry run python -m src.workers

review-test:
	@echo "Running review system smoke tests..."
	poetry run pytest \
		tests/legacy/src/application/services/test_modular_review_service.py \
		tests/legacy/src/application/use_cases/test_review_submission_use_case.py \
		tests/legacy/src/infrastructure/clients/test_llm_client.py \
		-v

review-e2e:
	@echo "Running review E2E tests..."
	@echo "Note: Requires MongoDB running (docker-compose up -d mongodb)"
	@echo "Note: Requires LLM_URL environment variable set"
	@echo "Tests will be skipped if MongoDB is unavailable"
	poetry run pytest tests/e2e/test_review_pipeline.py -v -m e2e

review-health-check:
	@echo "Running review system health check..."
	@echo "This will test all components: MongoDB, archives, diff, use cases, pipeline"
	@echo "Note: Full pipeline test requires LLM_URL environment variable"
	poetry run python scripts/quality/test_review_system.py
