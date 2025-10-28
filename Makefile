.PHONY: help install test lint format clean docker-build docker-up docker-down coverage integration e2e maintenance-cleanup maintenance-backup maintenance-export maintenance-validate day-07 day-08 mcp-discover mcp-demo test-mcp test-mcp-comprehensive mcp-chat mcp-chat-streaming mcp-server-start mcp-server-stop mcp-chat-docker mcp-demo-start mcp-demo-stop mcp-demo-logs demo-mcp-comprehensive

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
	poetry run pytest src/tests -v

unit:
	poetry run pytest src/tests/unit -v

integration:
	poetry run pytest src/tests/integration -v

e2e:
	poetry run pytest src/tests/e2e -v

coverage:
	poetry run pytest src/tests --cov=src --cov-report=html --cov-report=term-missing

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
