# 🏠 Local Models - TechxGenus/StarCoder2-7B-Instruct Service Infrastructure

This module provides the infrastructure for running TechxGenus/StarCoder2-7B-Instruct model locally with Docker. It's designed to serve as the backend for the multi-agent system in day_07.

## 🎯 Purpose

- **TechxGenus/StarCoder2-7B-Instruct Service**: Local hosting of instruction-tuned StarCoder model for code generation
- **Docker Orchestration**: Automated container management with security best practices
- **API Compatibility**: OpenAI-compatible chat API interface
- **Security**: Non-root user, optimized layers, health checks

## 📁 Structure

```
local_models/
├── chat_api.py                    # FastAPI server for all models
├── docker-compose.yml            # Docker Compose configuration
├── Dockerfile                    # Optimized Docker image with security
├── download_model.py             # Script for model pre-downloading
├── download_models.sh            # Management script for downloads
├── Dockerfile.download           # Docker image for downloading
├── docker-compose.download.yml   # Docker Compose for downloads
├── requirements.download.txt     # Minimal dependencies for downloading
├── DOWNLOAD_GUIDE.md             # Complete download guide
├── .env.example                  # Environment variables template
├── .env                         # Environment variables (create from example)
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Pre-download Models (Recommended)

For faster startup and offline usage, pre-download all models:

```bash
# Download all models to cache
./download_models.sh download-all

# Or download specific models
./download_models.sh download-model Qwen/Qwen1.5-4B-Chat
```

📖 **Detailed guide**: See [DOWNLOAD_GUIDE.md](DOWNLOAD_GUIDE.md) for complete instructions.

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your Hugging Face token
HF_TOKEN=your_huggingface_token_here
```

### 3. Start Chat Services

```bash
# Start all chat services
docker-compose up -d

# Or start specific services
docker-compose up -d qwen-chat mistral-chat tinyllama-chat starcoder-chat
```

### 4. Verify Services

```bash
# Check all services
curl http://localhost:8000/health  # Qwen
curl http://localhost:8001/health  # Mistral
curl http://localhost:8002/health  # TinyLlama
curl http://localhost:8003/health  # StarCoder

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'
```

## 🔒 Docker Security Features

The Dockerfile implements security best practices:

- **Non-root user**: Runs as `appuser` instead of root
- **Optimized layers**: Combined RUN commands to reduce image size
- **Health checks**: Built-in health monitoring
- **Minimal base**: Uses NVIDIA CUDA runtime with minimal dependencies
- **Proper ownership**: Files and directories have correct permissions

## 📊 Resource Requirements

- **GPU**: NVIDIA GPU with CUDA support
- **RAM**: 8-16GB recommended for StarCoder-7B
- **Storage**: ~15GB for model cache
- **Port**: 8003 (configurable in docker-compose.yml)

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
