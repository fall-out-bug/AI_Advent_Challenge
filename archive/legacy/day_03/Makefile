.PHONY: install run test clean help

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости через Poetry
	export PATH="/Users/fall_out_bug/.local/bin:$$PATH" && poetry install

run: ## Запустить чат с дедушкой v3.0
	export PATH="/Users/fall_out_bug/.local/bin:$$PATH" && poetry run python terminal_chat_v3.py

test: ## Запустить тесты
	export PATH="/Users/fall_out_bug/.local/bin:$$PATH" && poetry run pytest -v --cov=. --cov-report=term-missing

test-watch: ## Запустить тесты в режиме наблюдения
	export PATH="/Users/fall_out_bug/.local/bin:$$PATH" && poetry run pytest-watch

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	export PATH="/Users/fall_out_bug/.local/bin:$$PATH" && poetry env remove --all 2>/dev/null || true
