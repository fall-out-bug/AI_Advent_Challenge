# AI Advent Challenge

[English](README.md) | [Русский](README.ru.md)

> Ежедневные AI-проекты для изучения языковых моделей и мультиагентных систем

## Обзор

Этот репозиторий содержит **12 ежедневных задач** по созданию AI-систем с языковыми моделями. Каждый день вводит новые концепции и основывается на предыдущих задачах.

**Текущий статус:** ✅ День 12 - Система генерации PDF-дайджестов завершена

**Ключевые возможности:**
- ✅ 12 ежедневных задач от простого чата до production-ready системы PDF-дайджестов
- ✅ Clean Architecture с принципами SOLID
- ✅ 382+ тестов с 76%+ покрытием
- ✅ Поддержка множества моделей (StarCoder, Mistral, Qwen, TinyLlama)
- ✅ Интеграция MCP (Model Context Protocol)
- ✅ MCP-aware агент с автоматическим обнаружением и выполнением инструментов
- ✅ Telegram бот с FSM-based conversation flow
- ✅ Генерация PDF-дайджестов с автоматическим сбором постов
- ✅ Централизованная система логирования со структурированным выводом
- ✅ Мониторинг работоспособности и метрики dashboard

## Быстрый старт

```bash
# Установить зависимости
make install

# Запустить тесты
make test

# Запустить API
make run-api

# Запустить CLI
make run-cli
```

Подробные инструкции по настройке см. в [DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Структура проекта

```
AI_Challenge/
├── src/              # Clean Architecture Core
│   ├── domain/      # Слой бизнес-логики
│   ├── application/ # Use cases и orchestrators
│   ├── infrastructure/ # Внешние интеграции
│   └── presentation/   # API и CLI
├── tasks/           # Ежедневные задачи (day_01 - day_12)
├── local_models/    # Инфраструктура локальных моделей
├── shared/          # Унифицированный SDK для взаимодействия с моделями
├── scripts/         # Утилитарные скрипты
├── config/          # Конфигурационные файлы
└── docs/            # Полная документация
```

## Ежедневные задачи

| День | Область фокуса | Ключевые технологии | Статус |
|------|----------------|---------------------|--------|
| День 1 | Базовый чат-интерфейс | Python, API | ✅ Завершено |
| День 2 | JSON-структурированные ответы | Python, JSON parsing | ✅ Завершено |
| День 3 | Режим советника | Python, Управление сессиями | ✅ Завершено |
| День 4 | Контроль температуры | Python, Экспериментирование | ✅ Завершено |
| День 5 | Локальные модели | SDK, Docker, FastAPI | ✅ Завершено |
| День 6 | Тестовый фреймворк | Тестирование, Генерация отчетов | ✅ Завершено |
| День 7 | Мультиагентные системы | FastAPI, Docker, Оркестрация | ✅ Завершено |
| День 8 | Анализ токенов | Clean Architecture, ML Engineering | ✅ Завершено |
| День 9 | Интеграция MCP | MCP Protocol, Управление контекстом | ✅ Завершено |
| День 10 | Production-Ready MCP | Оркестрация, стриминг, кеширование | ✅ Завершено |
| День 11 | Butler Bot FSM | Telegram Bot, FSM, Intent Parsing | ✅ Завершено |
| День 12 | Система PDF-дайджестов | MongoDB, PDF Generation, MCP Tools | ✅ Завершено |

## Основная инфраструктура

### Локальные модели
- **Qwen-4B** (порт 8000) - Быстрые ответы, ~8GB RAM
- **Mistral-7B** (порт 8001) - Высокое качество, ~14GB RAM  
- **TinyLlama-1.1B** (порт 8002) - Компактный, ~4GB RAM
- **StarCoder-7B** (порт 9000) - Специализирован для генерации кода

### Общий SDK
Унифицированный SDK для взаимодействия с моделями во всех задачах.

```python
from shared.clients.model_client import ModelClient
client = ModelClient(provider="perplexity")
response = await client.chat("Привет, мир!")
```

## Текущие возможности (День 12)

**Система генерации PDF-дайджестов:**
- Генерация PDF-дайджестов через MCP инструменты (5 инструментов)
- Автоматический часовой сбор постов через `PostFetcherWorker`
- Гибридная дедупликация (message_id + content_hash)
- Кеширование PDF с TTL 1 час для мгновенной доставки
- Хранение в MongoDB с TTL 7 дней для автоматической очистки

**MCP-Aware Агент:**
- Автоматическое обнаружение инструментов через MCPToolsRegistry (кэш 5 минут)
- Выбор и выполнение инструментов на основе LLM
- Надежная логика повторных попыток с экспоненциальной задержкой
- Управление историей диалогов с автоматическим сжатием
- Интеграция метрик Prometheus

Быстрый старт:
```bash
# Убедитесь, что MongoDB запущен
docker-compose up -d mongodb

# Запустить post fetcher worker (часовой сбор)
python src/workers/post_fetcher_worker.py

# Или запустить бота для генерации PDF-дайджестов
make run-bot
```

См. [docs/day12/USER_GUIDE.md](docs/day12/USER_GUIDE.md) для руководства пользователя и [docs/day12/api.md](docs/day12/api.md) для документации API.

## Технологии

**Основные**: Python 3.10+, Poetry, Docker, FastAPI, Pydantic, pytest

**AI/ML**: HuggingFace Transformers, NVIDIA CUDA, 4-bit Quantization, Локальные модели

**Архитектура**: Clean Architecture, Domain-Driven Design, SOLID принципы

**Инфраструктура**: Traefik, NVIDIA Container Toolkit, Multi-stage Docker builds

## Документация

Основная документация:
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Настройка, деплой и операции
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Архитектура системы
- [USER_GUIDE.md](docs/USER_GUIDE.md) - Руководство пользователя
- [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - Справочник по API
- [AGENT_INTEGRATION.ru.md](docs/AGENT_INTEGRATION.ru.md) - Руководство по интеграции MCP-aware агента
- [MONITORING.md](docs/MONITORING.md) - Настройка мониторинга и Grafana дашборды
- [SECURITY.md](docs/SECURITY.md) - Политики безопасности и практики

Документация Дня 12:
- [Руководство пользователя PDF-дайджестов](docs/day12/USER_GUIDE.md)
- [API PDF-дайджестов](docs/day12/api.md)
- [Архитектура PDF-дайджестов](docs/day12/ARCHITECTURE.md)

См. [docs/INDEX.md](docs/INDEX.md) для полного индекса документации.

## Мониторинг

```bash
# Запустить стек мониторинга (Prometheus + Grafana)
docker-compose -f docker-compose.day12.yml up -d prometheus grafana

# Доступ к Grafana: http://localhost:3000 (admin/admin)
# Доступ к Prometheus: http://localhost:9090
```

Доступные дашборды:
1. **App Health** - Системные ресурсы, HTTP метрики, latency, доступность
2. **ML Service Metrics** - LLM inference latency, использование токенов, версионирование моделей
3. **Post Fetcher & PDF Metrics** - Метрики сбора постов и генерации PDF

См. [MONITORING.md](docs/MONITORING.md) для подробной настройки.

## Как внести свой вклад

Мы приветствуем вклад! См. [CONTRIBUTING.md](CONTRIBUTING.md) для подробных инструкций.

**Основные правила:**
- Следовать PEP 8 и Дзену Python
- Функции максимум 15 строк где возможно
- 100% покрытие типов
- 80%+ покрытие тестами
- Документировать все изменения

## Лицензия

Этот проект лицензирован под MIT License - см. файл LICENSE для деталей.

---

**Примечание**: Это обучающий проект для изучения AI и языковых моделей. Используйте ответственно и в соответствии с применимыми условиями использования.
