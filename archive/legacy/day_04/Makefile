.PHONY: install run test clean help

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости через Poetry (с фолбэком)
	@export PATH="$(HOME)/.local/bin:$$PATH"; \
	if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction || true; \
	else \
		python3 -m pip install --user --upgrade pip httpx pytest pytest-asyncio pytest-cov || true; \
	fi

run: ## Запустить чат v4
	@export PATH="$(HOME)/.local/bin:$$PATH"; \
	if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction || true; \
		poetry run python terminal_chat_v4.py || { echo "Poetry run failed, trying system python"; python3 -m pip install --user httpx || true; python3 terminal_chat_v4.py; }; \
	else \
		python3 -m pip install --user httpx || true; \
		python3 terminal_chat_v4.py; \
	fi


test: ## Запустить тесты
	@export PATH="$(HOME)/.local/bin:$$PATH"; \
	if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction || true; \
		poetry run pytest -v --cov=. --cov-report=term-missing || { echo "Poetry run failed, trying system python"; python3 -m pip install --user pytest pytest-asyncio pytest-cov httpx || true; pytest -v --cov=. --cov-report=term-missing; }; \
	else \
		python3 -m pip install --user pytest pytest-asyncio pytest-cov httpx || true; \
		pytest -v --cov=. --cov-report=term-missing; \
	fi

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +


