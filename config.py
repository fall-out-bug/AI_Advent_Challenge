"""
Конфигурация приложения
"""
import os
from pathlib import Path

# Путь к корневой директории проекта
BASE_DIR = Path(__file__).parent

# API ключ Perplexity
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Если ключ не найден в переменных окружения, попробуем загрузить из файла
if not PERPLEXITY_API_KEY:
    config_file = BASE_DIR / "api_key.txt"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                PERPLEXITY_API_KEY = f.read().strip()
        except Exception:
            PERPLEXITY_API_KEY = None

# Проверяем наличие ключа
def get_api_key():
    """Возвращает API ключ или None если не найден"""
    return PERPLEXITY_API_KEY

def is_api_key_configured():
    """Проверяет, настроен ли API ключ"""
    return PERPLEXITY_API_KEY is not None and PERPLEXITY_API_KEY.strip() != ""
