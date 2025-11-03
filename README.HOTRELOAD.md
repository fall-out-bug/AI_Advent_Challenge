# Hotreload для разработки

Этот файл описывает, как использовать hotreload для разработки Butler Agent.

## Что такое hotreload?

Hotreload позволяет автоматически перезагружать сервисы при изменении исходного кода без необходимости пересборки Docker образов.

## Использование

### Запуск с hotreload

```bash
# Запустить все сервисы с hotreload (кроме Mistral)
docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml up
```

### Запуск только отдельных сервисов с hotreload

```bash
# Только MCP Server с hotreload
docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml up mcp-server

# Только Butler Bot с hotreload
docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml up butler-bot
```

### Остановка

```bash
docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml down
```

## Как это работает

### MCP Server
- Использует `uvicorn --reload` для автоматической перезагрузки при изменении Python файлов
- Монтирует исходный код через volumes
- Отслеживает изменения в `/app/src`, `/app/shared`, `/app/config`

### Butler Bot
- Использует `watchdog` для отслеживания изменений файлов
- Автоматически перезапускает процесс при изменении `.py` файлов
- Игнорирует `__pycache__`, `.pyc` файлы и скрытые файлы

### Mistral
- **НЕ МОДИФИЦИРУЕТСЯ** - использует production образ без hotreload
- Это сделано для стабильности LLM сервиса

## Требования

- Python зависимости (`uvicorn`, `watchdog`) устанавливаются автоматически в контейнерах
- Исходный код должен быть доступен в текущей директории (`.`)

## Ограничения

1. **Изменения в зависимостях** (`pyproject.toml`) требуют пересборки образа:
   ```bash
   docker-compose -f docker-compose.butler.yml build mcp-server butler-bot
   ```

2. **Изменения в системных зависимостях** (apt пакеты) требуют пересборки

3. **Первый запуск** все равно требует сборки образов:
   ```bash
   docker-compose -f docker-compose.butler.yml build
   ```

## Troubleshooting

### Hotreload не работает

1. Проверьте, что файлы монтируются:
   ```bash
   docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml exec mcp-server ls -la /app/src
   ```

2. Проверьте логи на наличие ошибок:
   ```bash
   docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml logs -f mcp-server
   ```

3. Убедитесь, что используете правильные compose файлы:
   ```bash
   # Проверка текущей конфигурации
   docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml config
   ```

### Файлы не обновляются

- Проверьте права доступа к файлам
- Убедитесь, что используете `:rw` (read-write) mount, а не `:ro` (read-only)

### Ошибки импорта после hotreload

- Некоторые изменения могут требовать полного перезапуска контейнера
- Если возникают проблемы, перезапустите контейнер:
  ```bash
  docker-compose -f docker-compose.butler.yml -f docker-compose.butler.dev.yml restart mcp-server
  ```

