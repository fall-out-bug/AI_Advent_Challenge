.PHONY: help install test lint format clean docker-build docker-up docker-down coverage integration e2e maintenance-cleanup maintenance-backup maintenance-export maintenance-validate day-07 day-08

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
