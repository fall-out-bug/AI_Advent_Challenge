.PHONY: install test run demo clean setup

# Установка зависимостей
install:
	poetry install

# Запуск тестов
test:
	poetry run pytest tests/ -v --cov=src --cov-report=html

# Запуск тестирования моделей
run:
	poetry run python src/main.py

# Демонстрация системы
demo:
	poetry run python demo.py

# Очистка
clean:
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Создание структуры проекта
setup: install
	mkdir -p src tests
	@echo "Структура проекта создана"
