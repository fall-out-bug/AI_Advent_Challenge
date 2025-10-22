.PHONY: install chat clean

# Установка зависимостей
install:
	poetry install

# Запуск улучшенного терминального чата с дедушкой
chat:
	export PATH="/home/fall_out_bug/.local/bin:$PATH" && poetry run python terminal_chat_v2.py

# Очистка
clean:
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
