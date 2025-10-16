"""
Конфигурация приложения
"""
import os
from pathlib import Path

# Путь к корневой директории проекта
BASE_DIR = Path(__file__).parent

# API ключи
PERPLEXITY_API_KEY = None
CHAD_API_KEY = None

def load_api_key_from_file(file_path, key_name):
    """Загружает API ключ из файла, ищет строку с префиксом key_name:"""
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key_name}:") and len(line) > len(key_name) + 1:
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None

# Загружаем ключи из файла с явными префиксами
config_file = BASE_DIR / "api_key.txt"
if config_file.exists():
    PERPLEXITY_API_KEY = load_api_key_from_file(config_file, "perplexity")
    CHAD_API_KEY = load_api_key_from_file(config_file, "chadgpt")

# Если ключи не найдены в файле, попробуем переменные окружения
if not PERPLEXITY_API_KEY:
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not CHAD_API_KEY:
    CHAD_API_KEY = os.getenv("CHAD_API_KEY")

# Доступные API
AVAILABLE_APIS = ["perplexity", "chadgpt"]

def get_api_key(api_type="perplexity"):
    """Возвращает API ключ для указанного типа API"""
    if api_type == "perplexity":
        return PERPLEXITY_API_KEY
    elif api_type == "chadgpt":
        return CHAD_API_KEY
    return None

def is_api_key_configured(api_type="perplexity"):
    """Проверяет, настроен ли API ключ для указанного типа"""
    key = get_api_key(api_type)
    return key is not None and key.strip() != ""

def get_available_apis():
    """Возвращает список доступных API с настроенными ключами"""
    return [api for api in AVAILABLE_APIS if is_api_key_configured(api)]
