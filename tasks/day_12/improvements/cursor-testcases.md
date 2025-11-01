# Сценарии тестирования и checklist для Cursor

## Быстрый старт с генерацией кода

### Шаг 1: Инициализация проекта

```bash
# В корне репо
mkdir -p agent mcp_tools tests/unit tests/integration
touch .env Dockerfile docker-compose.yml
```

### Шаг 2: Структура каталогов

Попроси Cursor создать структуру:

```
Cursor Prompt:
"Создай полную файловую структуру проекта согласно спецификации.
Файлы должны иметь базовые заглушки с импортами и docstrings.
Используй type hints везде."
```

### Шаг 3: Генерация модулей

Для каждого модуля используй промпт типа:

```
Cursor Prompt:
"На основе спецификации в документе и примеров кода в code-examples.md
реализуй модуль agent/mcp_client.py.

Требования:
- Async HTTP клиент с retry логикой (tenacity)
- 5 методов для MCP tools
- Логирование через logging
- Type hints везде
- Docstrings в Google формате
- Обработка ошибок (MCPClientError, MCPTimeoutError и т.д.)
"
```

Повтори для:
- `agent/config.py` ✓ (в примерах)
- `agent/mcp_client.py` ✓ (в примерах)
- `agent/dialog_manager.py` ✓ (в примерах)
- `agent/agent.py` ✓ (в примерах)
- `mcp_tools/main.py` (FastAPI endpoints)
- `mcp_tools/tools/subscriptions.py` ✓ (в примерах)
- `mcp_tools/tools/posts.py` ✓ (в примерах)
- `mcp_tools/tools/collect.py` (collection trigger)
- `mcp_tools/tools/summarize.py` (Mistral inference)
- `mcp_tools/tools/export_pdf.py` (PDF generation)
- `mcp_tools/db/mongo.py` (MongoDB queries)
- `mcp_tools/db/redis.py` (Redis operations)

---

## Тест-кейсы для валидации

### Сценарий 1: Happy Path (весь пайплайн работает)

```
Вход:
- User: "собери дайджест по Набоке за 3 дня"
- Каналы доступны в DB
- Посты есть в нужном диапазоне

Ожидаемый результат:
✓ Agent успешно парсит намерение
✓ Находит канал "onaboka"
✓ Получает 10-20 постов
✓ Генерирует саммари
✓ Экспортирует PDF
✓ Возвращает path к файлу
```

**Команда для Cursor:**
```
"Напиши integration test happy_path для сценария выше.
Используй pytest + async fixtures + mock MCP tools.
Эмулируй MongoDB и Redis через testcontainers или monkeypatch."
```

---

### Сценарий 2: Канал не найден

```
Вход:
- User: "дайджест по НесуществующемуКаналу"
- Канал НЕ в DB

Ожидаемый результат:
✓ Agent вызывает get_subscriptions
✓ Не находит канал в списке
✓ Возвращает ошибку пользователю: "Канал не найден"
✓ Предлагает альтернативные названия (если есть похожие)
✓ Диалог не ломается, можно переспросить
```

**Команда для Cursor:**
```
"Напиши unit test для ошибки 'Channel not found'.
Мокируй get_subscriptions возвращаемым пустым списком.
Проверь, что агент возвращает понятное сообщение об ошибке."
```

---

### Сценарий 3: Посты не найдены, запускаем collection

```
Вход:
- User: "дайджест по Набоке"
- Канал найден
- Постов в DB нет (или < 5)

Ожидаемый результат:
✓ Agent первый раз вызывает get_posts → 404 или 0 постов
✓ Agent вызывает collect_posts(wait=True, timeout=30)
✓ Ждет 30 сек
✓ Повторно вызывает get_posts
✓ Если появились посты (≥ 5) → продолжает
✓ Если нет постов → ошибка "Не удалось получить посты"
```

**Команда для Cursor:**
```
"Напиши integration test для сценария collection retry.
Эмулируй:
1. Первый вызов get_posts возвращает HTTP 404
2. collect_posts возвращает status 202 (processing)
3. Второй вызов get_posts возвращает 15 постов
Проверь, что agent дожидается и продолжает."
```

---

### Сценарий 4: Dialog history переполнение

```
Вход:
- Dialog history > 8000 токенов
- User добавляет новое сообщение

Ожидаемый результат:
✓ Dialog manager обнаруживает переполнение
✓ Вызывает generate_summary на всем диалоге
✓ Заменяет историю на "[SUMMARY: ...]"
✓ Token count обнуляется
✓ Диалог продолжается с пустым контекстом
```

**Команда для Cursor:**
```
"Напиши unit test для dialog compression.
Создай фейковую историю с 100 сообщений (~100 токенов каждое).
Проверь:
1. Token count > лимита
2. should_summarize() вернет True
3. После compress_history() токены = 0
4. История содержит '[SUMMARY: ...]' сообщение"
```

---

### Сценарий 5: MongoDB недоступна

```
Вход:
- MongoDB сервис down
- User запрашивает дайджест

Ожидаемый результат:
✓ Agent попытается подключиться (retry 3 раза)
✓ После 3 попыток выдаст ошибку
✓ Сообщение: "Сервис недоступен, попробуйте позже"
✓ Логируется с full traceback
✓ Graceful degradation (не краш)
```

**Команда для Cursor:**
```
"Напиши test для обработки MongoDB timeout.
Используй monkeypatch чтобы эмулировать ConnectionError.
Проверь:
1. Retry логика срабатывает 3 раза
2. Exponential backoff между попытками
3. Возвращается понятная ошибка пользователю
4. Логируется полная информация об ошибке"
```

---

### Сценарий 6: Redis недоступна

```
Вход:
- Redis сервис down
- User запрашивает дайджест (кэш не нужен, все OK)

Ожидаемый результат:
✓ Agent продолжает работать БЕЗ Redis
✓ Все операции выполняются медленнее (нет кэша)
✓ Логируется warning "Redis unavailable, working without cache"
✓ Диалог и посты ОСТАЮТСЯ в MongoDB (не теряются)
```

**Команда для Cursor:**
```
"Напиши test для graceful degradation без Redis.
Монопатчируй Redis connection чтобы она не доступна.
Проверь:
1. Agent все равно завершает пайплайн
2. Логируется warning про Redis
3. Posts кэшируются в MongoDB, а не Redis"
```

---

### Сценарий 7: MCP Tools server не доступен

```
Вход:
- MCP Tools сервер в контейнере упал (port 8001-8004 не слушают)
- User запрашивает дайджест

Ожидаемый результат:
✓ MCPClient пытается подключиться → connection refused
✓ Retry логика срабатывает 3 раза
✓ Экспоненциальный backoff: 2сек, 4сек, 8сек
✓ После истечения → MCPTimeoutError
✓ Agent возвращает пользователю: "Сервис обработки недоступен"
```

**Команда для Cursor:**
```
"Напиши test для MCP Tools unavailability.
Используй pytest-aiohttp чтобы эмулировать connection refused.
Проверь retry backoff логику:
- 1я попытка: 2-4 сек ожидание
- 2я попытка: 4-8 сек ожидание  
- 3я попытка: 8-16 сек ожидание
Всего макс ~30 сек перед ошибкой."
```

---

### Сценарий 8: Mistral inference падает

```
Вход:
- Mistral модель возвращает error
- MCP /tools/generate_summary возвращает 503

Ожидаемый результат:
✓ Agent ловит ошибку
✓ Логирует full error details
✓ Возвращает пользователю: "Ошибка обработки: не удалось создать саммари"
✓ Предлагает повторить позже
✓ Диалог история СОХРАНЯЕТСЯ для отладки
```

**Команда для Cursor:**
```
"Напиши test для Mistral inference error.
Мокируй generate_summary чтобы вернуть:
{
  'status': 'error',
  'error': 'Model inference timed out',
  'code': 'MODEL_ERROR'
}
HTTP 503

Проверь:
1. Agent ловит исключение
2. Возвращает user-friendly ошибку
3. История сохранена в MongoDB
4. Можно повторить запрос после восстановления"
```

---

### Сценарий 9: PDF export fails

```
Вход:
- Саммари готова
- /tools/export_pdf возвращает 400 Bad Request

Ожидаемый результат:
✓ Agent ловит ошибку
✓ Возвращает саммари в текстовом виде
✓ Сообщение: "PDF не создалась, вот текст саммари: [текст]"
✓ Пользователь не теряет результат работы
```

**Команда для Cursor:**
```
"Напиши fallback для PDF export failure.
Если export_pdf вернет ошибку, агент должен:
1. Залогировать ошибку
2. Вернуть пользователю текст саммари напрямую
3. Сказать пользователю 'PDF не создалась'
Напиши test для этого сценария."
```

---

### Сценарий 10: Очень большой диалог

```
Вход:
- Пользователь уже вел 50+ сообщений диалога
- Диалог > 16000 токенов
- User добавляет новый запрос

Ожидаемый результат:
✓ Dialog manager обнаруживает что диалог ОЧЕНЬ большой
✓ Вызывает summarize()
✓ Заменяет всю историю одним summary сообщением
✓ Token count ≤ 1000
✓ Новый запрос обрабатывается в "чистом" контексте
✓ История сохраняется в архиве (старый диалог не теряется)
```

**Команда для Cursor:**
```
"Напиши extended test для очень большого диалога.
1. Создай 50 фейковых сообщений (итого ~10000 токенов)
2. Проверь что should_summarize() вернет True
3. После compression token count должен быть < 1000
4. Старая история должна сохраниться в 'compressed_at' поле
5. Новое сообщение обрабатывается корректно"
```

---

## Checklist для запуска

### Before First Run

- [ ] Docker и docker-compose установлены
- [ ] Достаточно GPU VRAM для Mistral-7B (~8GB для fp16 или ~4GB для q4)
- [ ] Все переменные в .env заполнены
- [ ] Не забыл создать `init-mongo.js` файл

### Docker Compose Up

- [ ] MongoDB поднялась (healthcheck passed)
- [ ] Redis поднялся (healthcheck passed)
- [ ] MCP Tools сервер запустился (logs: "Uvicorn running on 0.0.0.0:8001")
- [ ] Agent контейнер запустился (logs: "Agent initialized")

### MCP Tools Server Health Checks

```bash
# Проверить каждый endpoint
curl -X POST http://localhost:8001/tools/get_subscriptions \
  -H "Content-Type: application/json" \
  -d '{}'

curl -X POST http://localhost:8002/tools/get_posts \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "onaboka", "limit": 10}'

# И т.д. для остальных
```

- [ ] Все endpoints возвращают 200 OK (или ожидаемые ошибки)
- [ ] Логи сервера чистые (нет exceptions)

### Agent Tests

- [ ] Unit tests проходят: `pytest tests/unit -v`
- [ ] Integration tests проходят: `pytest tests/integration -v`
- [ ] Coverage > 80%: `pytest --cov=agent --cov=mcp_tools`

### Manual E2E Test

```bash
# Вход в контейнер agent
docker exec -it agent_mistral python main.py

# Тип в интерпретаторе
>> user_input = "собери дайджест по Набоке за 3 дня"
>> response = await agent.process_user_input(user_input)
>> print(response)
```

- [ ] Получен PDF файл
- [ ] Путь указан корректно в `/output/digest_*.pdf`
- [ ] Диалог история сохранилась в MongoDB
- [ ] Нет ошибок в логах

---

## Метрики для мониторинга

После первого запуска, мониторь:

1. **Agent performance:**
   - Время выполнения пайплайна (target: < 60 сек)
   - Количество retry-ей (target: 0-1 на запрос)
   - Токены в контексте (target: < 8000)

2. **MCP Tools:**
   - HTTP response time каждого endpoint (target: < 5 сек)
   - Кэш hit rate для get_posts (target: > 50%)

3. **Storage:**
   - MongoDB collection sizes
   - Redis memory usage
   - Output PDF files directory size

4. **Errors:**
   - Error rates по типам (ConnectionError, TimeoutError и т.д.)
   - Stack traces для критических ошибок

---

## Промпты для расширенной функциональности (Phase 2)

После базовой реализации можно добавить:

### A. Web UI для Agent

```
Cursor Prompt:
"Создай FastAPI веб-интерфейс для Agent.
- POST /chat endpoint для пользовательского ввода
- GET /session/{session_id}/history для истории
- WebSocket для real-time обновлений
- Frontend на Streamlit или React (выбери)"
```

### B. Background Jobs для Collection

```
Cursor Prompt:
"Реализуй Celery + Redis для фонового сбора постов.
- Celery tasks для collect_posts
- Периодические задачи через celery-beat
- Мониторинг через flower"
```

### C. Metrics и Observability

```
Cursor Prompt:
"Добавь Prometheus metrics и Grafana dashboard.
- HTTP request metrics для всех endpoints
- MongoDB query times
- Agent pipeline duration
- Create простой Grafana dashboard"
```

### D. Advanced Dialog Management

```
Cursor Prompt:
"Реализуй context-aware summarization.
- Извлечение ключевых entities (каналы, даты, тематики)
- Сохранение контекста между сессиями
- Рекомендации на основе истории"
```

---

## Документирование кода

Когда основной код готов, проси Cursor:

```
Cursor Prompt:
"Добавь docstrings, type hints и комментарии в ВСЕ функции.
Используй Google style docstrings с примерами.
После этого сгенерируй HTML документацию через Sphinx."
```

---

## Финальная валидация

```bash
# 1. Linting
flake8 agent/ mcp_tools/ --max-line-length=100
black --check agent/ mcp_tools/

# 2. Type checking
mypy agent/ mcp_tools/ --ignore-missing-imports

# 3. Security
bandit -r agent/ mcp_tools/

# 4. Tests
pytest tests/ -v --cov

# 5. Docker build
docker-compose build

# 6. Runtime
docker-compose up -d
docker-compose logs --tail=50
```

- [ ] Все линтеры проходят
- [ ] Контейнеры собираются без warnings
- [ ] E2E тест выполняется успешно
- [ ] Документация сгенерирована
