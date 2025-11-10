# Homework Review System - Quick Start

> ⚠️ Local model containers are deprecated in favor of shared infrastructure. Legacy manifests now live in `archive/legacy/local_models/`; commands below are kept for reference.

## 🚀 Быстрый старт

### 1. Поднять общее окружение

```bash
# Рекомендуемый способ (обёртка внутри AI Challenge)
./scripts/start_shared_infra.sh

# Альтернатива (из репозитория infra)
cd ~/work/infra
set -a && source .env.infra && set +a
make day-12-up
```

Скрипт поднимет MongoDB, Prometheus, Grafana и reviewer API в общем docker-compose
окружении и прогрузит переменные `MONGODB_URL`, `PROMETHEUS_URL`, `LLM_API_URL`.

### 2. Проверить доступность сервисов

```bash
# Примеры быстрых проверок после запуска
curl "${PROMETHEUS_URL:-http://127.0.0.1:9090}/-/ready"
poetry run python scripts/test_review_system.py | tail -n 20
```

Если тестовый скрипт завершается с сообщением `✅ All tests passed!`, инфраструктура
готова к работе. При ошибках проверьте, что `scripts/start_shared_infra.sh` отработал без
ошибок и что Docker-контейнеры `infra_*` запущены.

### 3. Протестировать ревью на реальном архиве

```bash
poetry run python scripts/test_review_system.py
```

Скрипт прогонит несколько проверок (MongoDB, анализ архива, полный пайплайн) с использованием
модульного reviewer сервиса. Для запуска собственного архива используйте MCP инструмент
`review_homework_archive` или новый CLI backoffice сценарий (см. `docs/API_MCP.md`).

### 4. Использовать через MCP

Tool автоматически доступен в MCP server:

```python
from src.presentation.mcp.tools.homework_review_tool import review_homework_archive

result = await review_homework_archive(
    archive_path="/path/to/archive.zip",
    assignment_type="auto",  # или "HW1", "HW2", "HW3"
    token_budget=8000,
    model_name="mistral"
)

print(result["markdown_report"])
```

## 📊 Что делает система

1. **Pass 1 (Architecture)**: Обнаруживает компоненты (Docker, Airflow, Spark, MLflow)
2. **Pass 2 (Components)**: Детальный анализ каждого компонента
3. **Pass 3 (Synthesis)**: Синтез всех findings и финальные рекомендации

## 📁 Структура результатов

После выполнения создается:
- `<archive_name>_review.md` - Полный отчет в Markdown
- Session сохраняется в `/tmp/sessions/<session_id>/`

## 🔧 Требования

- Docker и Docker Compose (используются стэком `~/work/infra`)
- Python 3.10 + Poetry (для запуска скриптов и CLI)
- Доступ к общему `.env.infra` (см. `scripts/start_shared_infra.sh`)

## 📚 Документация

- `docs/MCP_TOOL_USAGE.md` - Использование через MCP
- `docs/MODEL_SETUP.md` - Настройка моделей
- `docs/PHASE_1_IMPLEMENTATION.md` - Архитектура системы
- `docs/TESTING_FIXTURES_GUIDE.md` - Тестовые фикстуры

## 🐛 Troubleshooting

### Модель не запускается

```bash
# Проверить логи
docker logs local_models-mistral-chat-1

# Перезапустить
cd archive/legacy/local_models
docker-compose restart mistral-chat
```

### Health endpoint не отвечает

Модель может еще загружаться. Проверьте логи:
```bash
docker logs -f local_models-mistral-chat-1
```

Ожидайте сообщения "Model loaded" или "Server started".

### Порт 8001 занят

Измените порт в `archive/legacy/local_models/docker-compose.yml`:
```yaml
ports:
  - "8002:8000"  # Изменить 8001 на 8002
```

И обновите конфигурацию в `shared/shared_package/config/models.py`.
