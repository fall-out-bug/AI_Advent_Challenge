# Day 05 - Terminal Chat with Local Models
# Based on universal Makefile template

.PHONY: help install test run-models stop-models clean run run-zen check-models logs demo-tokens demo-api demo-history

# Project-specific variables
PROJECT_NAME := day-05-terminal-chat
MAIN_SCRIPT := terminal_chat_v5.py
ZEN_SCRIPT := terminal_chat_v5_zen.py
TEST_DIR := tests
REQUIREMENTS_FILE := requirements.txt

# Detect Python executable
PYTHON := $(shell which python3 || which python)
PIP := $(shell which pip3 || which pip)

# Colors for output
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Показать справку
	@echo "$(GREEN)Доступные команды для $(PROJECT_NAME):$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)Installing dependencies...$(RESET)"
	$(PIP) install -r $(REQUIREMENTS_FILE)

test: ## Запустить тесты
	@echo "$(GREEN)Running tests...$(RESET)"
	$(PYTHON) -m pytest tests/ -v

test-zen: ## Запустить тесты для Zen-версии
	@echo "$(GREEN)Running Zen tests...$(RESET)"
	$(PYTHON) -m pytest tests/test_terminal_chat_v5_zen.py tests/test_chat_logic.py tests/test_terminal_ui.py tests/test_chat_state.py tests/test_text_utils.py -v

test-coverage: ## Запустить тесты с покрытием
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	$(PYTHON) -m pytest tests/ --cov=. --cov-report=html --cov-report=term

docs: ## Генерировать документацию
	@echo "$(GREEN)Generating documentation...$(RESET)"
	@echo "📚 Available documentation:"
	@echo "  • API_DOCUMENTATION.md - Complete API reference"
	@echo "  • DEVELOPER_GUIDE.md - Development guidelines"
	@echo "  • CHANGELOG.md - Version history"
	@echo "  • README.md - User guide"

lint: ## Проверить код линтером
	@echo "$(GREEN)Running linter...$(RESET)"
	$(PYTHON) -m flake8 business/ ui/ state/ utils/ --max-line-length=100

format: ## Форматировать код
	@echo "$(GREEN)Formatting code...$(RESET)"
	$(PYTHON) -m black business/ ui/ state/ utils/ tests/

type-check: ## Проверить типы
	@echo "$(GREEN)Running type checker...$(RESET)"
	$(PYTHON) -m mypy business/ ui/ state/ utils/ --ignore-missing-imports

run: ## Запустить чат (оригинальная версия)
	@echo "$(GREEN)Running $(PROJECT_NAME)...$(RESET)"
	$(PYTHON) $(MAIN_SCRIPT)

run-models: ## Запустить локальные модели
	@echo "$(GREEN)Starting local models...$(RESET)"
	cd ../local_models && docker-compose up -d

stop-models: ## Остановить локальные модели
	@echo "$(GREEN)Stopping local models...$(RESET)"
	cd ../local_models && docker-compose down

check-models: ## Проверить статус локальных моделей
	@echo "$(GREEN)Checking model availability...$(RESET)"
	@curl -s http://localhost:8000/chat > /dev/null && echo "✅ Qwen (8000) - доступна" || echo "❌ Qwen (8000) - недоступна"
	@curl -s http://localhost:8001/chat > /dev/null && echo "✅ Mistral (8001) - доступна" || echo "❌ Mistral (8001) - недоступна"
	@curl -s http://localhost:8002/chat > /dev/null && echo "✅ TinyLlama (8002) - доступна" || echo "❌ TinyLlama (8002) - недоступна"

logs: ## Показать логи локальных моделей
	@echo "$(GREEN)Showing model logs...$(RESET)"
	cd ../local_models && docker-compose logs -f

demo-tokens: ## Показать демонстрацию работы с токенами
	@echo "$(GREEN)Running token demo...$(RESET)"
	$(PYTHON) demo_tokens.py

demo-api: ## Показать демонстрацию единообразного переключения API
	@echo "$(GREEN)Running API switching demo...$(RESET)"
	$(PYTHON) demo_api_switching.py

demo-history: ## Показать демонстрацию работы с историей сообщений
	@echo "$(GREEN)Running history demo...$(RESET)"
	$(PYTHON) demo_history.py

clean: ## Очистить кэш и временные файлы
	@echo "$(GREEN)Cleaning up...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

setup: install ## Setup project (install dependencies)
	@echo "$(GREEN)Project setup complete!$(RESET)"

run-zen: ## Run Zen version of terminal chat (Python Zen compliant)
	@echo "$(GREEN)🐍 Starting Zen version of terminal chat...$(RESET)"
	@echo "$(YELLOW)Following Python Zen: Simple, Explicit, Beautiful$(RESET)"
	@$(PYTHON) $(ZEN_SCRIPT)

run: ## Run terminal chat (original version)
	@echo "$(GREEN)Starting terminal chat...$(RESET)"
	@$(PYTHON) $(MAIN_SCRIPT)

check-python: ## Check Python version
	@echo "$(GREEN)Python version:$(RESET)"
	@$(PYTHON) --version
