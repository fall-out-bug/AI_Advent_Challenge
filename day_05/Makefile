.PHONY: help install test run-models stop-models clean

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r requirements.txt

test: ## Запустить тесты
	python -m pytest tests/test_chat_v5.py -v

run-models: ## Запустить локальные модели
	cd local_models && docker-compose up -d

stop-models: ## Остановить локальные модели
	cd local_models && docker-compose down

clean: ## Очистить кэш и временные файлы
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

run: ## Запустить чат (требует запущенные модели)
	python terminal_chat_v5.py

check-models: ## Проверить статус локальных моделей
	@echo "Проверка доступности моделей..."
	@curl -s http://localhost:8000/chat > /dev/null && echo "✅ Qwen (8000) - доступна" || echo "❌ Qwen (8000) - недоступна"
	@curl -s http://localhost:8001/chat > /dev/null && echo "✅ Mistral (8001) - доступна" || echo "❌ Mistral (8001) - недоступна"
	@curl -s http://localhost:8002/chat > /dev/null && echo "✅ TinyLlama (8002) - доступна" || echo "❌ TinyLlama (8002) - недоступна"

logs: ## Показать логи локальных моделей
	cd local_models && docker-compose logs -f

demo-tokens: ## Показать демонстрацию работы с токенами
	python demo_tokens.py

demo-api: ## Показать демонстрацию единообразного переключения API
	python demo_api_switching.py

demo-history: ## Показать демонстрацию работы с историей сообщений
	python demo_history.py
