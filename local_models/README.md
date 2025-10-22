# 🏠 Local Models - Базовая инфраструктура локальных языковых моделей

Этот модуль содержит базовую инфраструктуру для работы с локальными языковыми моделями. Он предоставляет единообразный API для различных моделей и может использоваться любыми проектами в репозитории.

## 🎯 Назначение

- **Единообразный API**: Стандартизированный интерфейс для всех локальных моделей
- **Docker-оркестрация**: Автоматическое управление контейнерами с моделями
- **Масштабируемость**: Легкое добавление новых моделей
- **Изоляция**: Независимость от внешних API и интернета

## 📁 Структура

```
local_models/
├── chat_api.py          # FastAPI сервер для локальных моделей
├── docker-compose.yml   # Конфигурация Docker Compose
├── Dockerfile          # Образ для запуска моделей
├── download_model.py   # Скрипт для предварительной загрузки моделей
└── README.md           # Этот файл
```

## 🚀 Быстрый старт

### 1. Запуск всех моделей

```bash
# Из корня репозитория
cd local_models
docker-compose up -d
```

### 2. Проверка доступности

```bash
# Проверить статус всех моделей
curl http://localhost:8000/chat  # Qwen
curl http://localhost:8001/chat  # Mistral  
curl http://localhost:8002/chat  # TinyLlama
```

### 3. Использование в проектах

```python
# В любом проекте репозитория
import httpx

async def call_local_model(model_name: str, messages: list):
    port = {"qwen": 8000, "mistral": 8001, "tinyllama": 8002}[model_name]
    url = f"http://localhost:{port}/chat"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        })
        return response.json()
```

## 🤖 Поддерживаемые модели

| Модель | Порт | RAM | Описание |
|--------|------|-----|----------|
| **Qwen-4B** | 8000 | ~8GB | Быстрые ответы, хорошее качество |
| **Mistral-7B** | 8001 | ~14GB | Высокое качество, рекомендована |
| **TinyLlama-1.1B** | 8002 | ~4GB | Компактная, быстрая |

## 🔧 Архитектура

### FastAPI Сервер (`chat_api.py`)

- **Единый эндпоинт**: `/chat` для всех моделей
- **OpenAI-совместимый API**: Стандартный формат запросов
- **Автоматическое форматирование**: Поддержка разных форматов промптов
- **Квантизация**: 4-bit квантизация для экономии памяти

### Docker Оркестрация

- **Общий кэш**: Все модели используют общий volume для HuggingFace кэша
- **GPU поддержка**: Автоматическое использование NVIDIA GPU
- **Изоляция**: Каждая модель в отдельном контейнере

### Форматы промптов

Автоматическое определение формата на основе имени модели:

- **Mistral**: `<s>[INST] <<SYS>>...<</SYS>>...[/INST]`
- **Qwen**: `<|im_start|>system...<|im_end|>...`
- **TinyLlama**: `<|system|>...<|user|>...<|assistant|>`

## 📊 API Спецификация

### Запрос

```json
POST /chat
{
    "messages": [
        {"role": "system", "content": "Ты полезный ассистент"},
        {"role": "user", "content": "Привет!"}
    ],
    "max_tokens": 500,
    "temperature": 0.7
}
```

### Ответ

```json
{
    "response": "Привет! Как дела?",
    "response_tokens": 5,
    "input_tokens": 12,
    "total_tokens": 17
}
```

## 🛠️ Управление

### Команды Docker Compose

```bash
# Запуск всех моделей
docker-compose up -d

# Остановка всех моделей  
docker-compose down

# Просмотр логов
docker-compose logs -f

# Перезапуск конкретной модели
docker-compose restart qwen-chat
```

### Мониторинг

```bash
# Проверка статуса
docker-compose ps

# Использование ресурсов
docker stats

# Логи конкретной модели
docker-compose logs qwen-chat
```

## 🔧 Настройка

### Переменные окружения

- `MODEL_NAME`: Имя модели из HuggingFace
- `HF_TOKEN`: Токен для доступа к приватным моделям
- `CUDA_VISIBLE_DEVICES`: Управление GPU

### Добавление новой модели

1. Добавить сервис в `docker-compose.yml`:
```yaml
new-model-chat:
  build: .
  ports:
    - "8003:8000"
  environment:
    - MODEL_NAME=your/model-name
```

2. Обновить маппинг портов в проектах:
```python
MODEL_PORTS = {
    "qwen": 8000,
    "mistral": 8001, 
    "tinyllama": 8002,
    "new-model": 8003  # Новый порт
}
```

## 🧪 Тестирование

### Проверка работоспособности

```bash
# Тест всех моделей
for port in 8000 8001 8002; do
  echo "Testing port $port..."
  curl -X POST http://localhost:$port/chat \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10}'
done
```

### Бенчмарки

```python
import asyncio
import time
import httpx

async def benchmark_model(model_name: str, num_requests: int = 10):
    port = {"qwen": 8000, "mistral": 8001, "tinyllama": 8002}[model_name]
    url = f"http://localhost:{port}/chat"
    
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(num_requests):
            task = client.post(url, json={
                "messages": [{"role": "user", "content": "Test message"}],
                "max_tokens": 50
            })
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    avg_time = total_time / num_requests
    
    print(f"{model_name}: {avg_time:.2f}s per request")
    return avg_time
```

## 🚨 Устранение неполадок

### Модель не запускается

1. Проверить доступность GPU:
```bash
nvidia-smi
```

2. Проверить свободную память:
```bash
free -h
```

3. Проверить логи:
```bash
docker-compose logs model-name
```

### Медленные ответы

1. Увеличить `max_tokens` для более длинных ответов
2. Уменьшить `temperature` для более детерминированных ответов
3. Проверить загрузку GPU: `nvidia-smi`

### Ошибки памяти

1. Использовать меньшую модель (TinyLlama)
2. Уменьшить `max_tokens`
3. Перезапустить контейнеры

## 📈 Производительность

### Рекомендуемые настройки

- **Для разработки**: TinyLlama (быстро, мало памяти)
- **Для продакшена**: Mistral (качество/скорость)
- **Для экспериментов**: Qwen (баланс)

### Оптимизация

- Используйте SSD для кэша моделей
- Выделите достаточно RAM (16GB+ рекомендуется)
- Настройте `CUDA_VISIBLE_DEVICES` для изоляции GPU

## 🔗 Интеграция с проектами

Этот модуль используется в:
- `day_05/` - Основная интеграция с чат-ботом
- Будущие проекты могут легко подключаться к локальным моделям

### Пример интеграции

```python
# В любом проекте
from local_models.client import LocalModelClient

client = LocalModelClient()
response = await client.chat("qwen", [
    {"role": "user", "content": "Привет!"}
])
```

---

**💡 Совет**: Этот модуль спроектирован как базовая инфраструктура. Добавляйте новые модели и функции по мере необходимости!
