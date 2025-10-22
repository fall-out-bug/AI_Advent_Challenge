.PHONY: setup help

# Создать api_key.txt из шаблона
setup:
	cp api_key.txt.example api_key.txt
	@echo "Создан api_key.txt. Пожалуйста, добавьте ваш API ключ Perplexity в этот файл."

# Показать справку
help:
	@echo "AI Challenge - коллекция проектов по работе с AI API"
	@echo ""
	@echo "Команды:"
	@echo "  make setup     - Создать api_key.txt из шаблона"
	@echo "  make help      - Показать эту справку"
	@echo ""
	@echo "Проекты:"
	@echo "  day_01/        - Терминальный чат с ехидным AI-дедушкой"
	@echo ""
	@echo "Для работы с конкретным проектом перейдите в его папку и следуйте инструкциям в README."
