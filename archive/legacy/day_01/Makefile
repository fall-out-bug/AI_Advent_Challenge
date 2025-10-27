.PHONY: install chat clean setup

# Установка зависимостей
install:
	poetry install

# Запуск терминального чата с дедушкой
chat:
	export PATH="/home/fall_out_bug/.local/bin:$PATH" && poetry run python terminal_chat.py

# Очистка
clean:
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Создание файла API ключа
setup:
	cp api_key.txt.example api_key.txt
	@echo "Добавьте ваш API ключ в api_key.txt"
