# Epic 24 · Интеграция голосовых команд

## Обзор
Epic 24 фокусируется на интеграции поддержки голосовых команд в Butler Telegram бот с использованием Whisper Speech-to-Text (STT) транскрипции. Эпик реализует автоматическую транскрипцию голосовых сообщений и немедленное выполнение команд без подтверждения пользователя.

## Ключевые возможности
- ✅ **Интеграция Whisper STT** для транскрипции голосовых сообщений
- ✅ **Автоматическое выполнение команд** после транскрипции
- ✅ **Хранение команд в Redis** с TTL
- ✅ **GPU-ускоренная транскрипция** с использованием CUDA
- ✅ **Реализация Clean Architecture** с Protocol-based дизайном
- ✅ **Асинхронная загрузка модели** для предотвращения блокировки при старте
- ✅ **Кеширование модели** через Docker volumes

## Документация
- [Epic 24 Summary](./epic_24.md) - Полное описание целей, архитектурных решений и реализации
- [Review Materials](./REVIEW.md) - Детальные материалы для ревью и обзор реализации
- [Tech Lead Final Review](./tech_lead_final_review.md) - Финальное ревью техлида и одобрение
- [Final Acceptance Matrix](./acceptance_matrix_final.md) - Финальные критерии приемки и доказательства
- [Epic Closure](./epic_closure.md) - Документ закрытия эпика и подпись

## Быстрая справка

### Поток голосовых команд
1. **Пользователь отправляет голосовое сообщение** → Бот загружает аудио файл
2. **Аудио транскрибируется** через Whisper STT API (`/api/transcribe`)
3. **Текст сохраняется в Redis** временно (TTL: 5 минут)
4. **Команда автоматически выполняется** через ButlerOrchestrator
5. **Результат отправляется пользователю** через Telegram Bot API

### Архитектурные слои

#### Domain Layer
- **Протоколы** (`src/domain/interfaces/voice.py`):
  - `SpeechToTextAdapter`: Протокол STT транскрипции
  - `VoiceCommandStore`: Протокол хранения команд
  - `ButlerGateway`: Протокол маршрутизации Butler
  - `ConfirmationGateway`: Протокол подтверждения (устарел)
- **Value Objects** (`src/domain/value_objects/transcription.py`):
  - `Transcription`: Результат транскрипции с текстом, уверенностью, языком, длительностью

#### Application Layer
- **DTOs** (`src/application/voice/dtos.py`):
  - `ProcessVoiceCommandInput`, `HandleVoiceConfirmationInput`, `TranscriptionOutput`
- **Use Cases** (`src/application/voice/use_cases/`):
  - `ProcessVoiceCommandUseCase`: Обработка голосовых сообщений, транскрипция, сохранение в Redis
  - `HandleVoiceConfirmationUseCase`: Обработка подтверждений, маршрутизация в Butler

#### Infrastructure Layer
- **Адаптеры** (`src/infrastructure/voice/`):
  - `WhisperSpeechToTextAdapter`: HTTP клиент для Whisper STT API
  - `RedisVoiceCommandStore`: Хранилище Redis с TTL
  - `ButlerGatewayImpl`: Реализация маршрутизации Butler
  - `ConfirmationGatewayImpl`: Telegram сообщения подтверждения (устарел)
- **Factory** (`src/infrastructure/voice/factory.py`):
  - `create_voice_use_cases()`: Создание use cases с зависимостями

#### Presentation Layer
- **Voice Handler** (`src/presentation/bot/handlers/voice_handler.py`):
  - `handle_voice_message()`: Обработка голосовых/аудио сообщений
  - `handle_voice_callback()`: Обработка callback подтверждений (устарел)
  - `setup_voice_handler()`: Настройка роутера с use cases

### Whisper STT Сервер
- **Расположение**: `docker/whisper-server/`
- **Эндпоинты**:
  - `GET /health`: Проверка работоспособности со статусом загрузки модели
  - `POST /api/transcribe`: Транскрибировать аудио файл
- **Конфигурация**:
  - Модель: `base` (оптимизирована для русского языка)
  - GPU: Поддержка CUDA включена
  - Volume: `whisper-model-cache` для персистентности модели

### Конфигурация
**Переменные окружения** (в `docker-compose.butler.yml`):
- `WHISPER_HOST`: Адрес сервиса Whisper STT (по умолчанию: `whisper-stt`)
- `WHISPER_PORT`: Порт API Whisper STT (по умолчанию: `8005`)
- `STT_MODEL`: Имя модели Whisper (по умолчанию: `base`)
- `REDIS_HOST`: Хост Redis для хранения команд (по умолчанию: `shared-redis`)
- `REDIS_PORT`: Порт Redis (по умолчанию: `6379`)
- `REDIS_PASSWORD`: Пароль Redis (опционально)

**Настройки** (в `src/infrastructure/config/settings.py`):
- Все переменные окружения доступны через класс `Settings` с type hints и валидацией

### Хранилище Redis
- **Формат ключа**: `voice:command:{user_id}:{command_id}`
- **Формат значения**: JSON `{"text": "транскрибированный текст"}`
- **TTL**: 300 секунд (5 минут) по умолчанию
- **Назначение**: Временное хранение транскрибированных команд перед выполнением Butler

## Статус
**Статус**: ✅ **Завершён и закрыт**
**Дата завершения**: 2025-11-18
**Статус ревью**: ✅ **Одобрено для продакшена**
**Интеграция**: ✅ Все интеграции восстановлены и работают
**Готовность к продакшену**: ✅ Да

### Финальный статус (2025-11-18)
- ✅ **Whisper STT**: Работает с моделью `base`, закеширована и готова
- ✅ **Voice Handler**: Инициализирован и обрабатывает голосовые сообщения
- ✅ **Redis**: Подключение с аутентификацией работает корректно
- ✅ **MongoDB**: Подключение с аутентификацией работает корректно
- ✅ **Butler Bot**: Обрабатывает голосовые команды и автоматически выполняет их
- ✅ **Интеграционное тестирование**: Протестировано в продакшен-подобной среде, стабильно

### Исправленные проблемы
1. **TypeError с `audio_data.read()`**: Исправлена обработка bytes vs file-like объектов из `aiogram.download_file()`
2. **Ошибка аутентификации Redis**: Добавлены явные переменные окружения для учетных данных Redis
3. **MongoDB OperationFailure**: Добавлены учетные данные MongoDB в строку подключения
4. **Ошибки сборки Docker**: Исправлены зависимости путей в Dockerfile.bot и numpy в требованиях Whisper
5. **Потеря интеграций**: Восстановлены все интеграции после временного удаления

## Компоненты

### Реализованные файлы

#### Domain Layer
- `src/domain/interfaces/voice.py` - Протоколы голосовых команд
- `src/domain/value_objects/transcription.py` - Value object транскрипции

#### Application Layer
- `src/application/voice/dtos.py` - DTOs голосовых команд
- `src/application/voice/use_cases/process_voice_command.py` - Use case обработки голосовой команды
- `src/application/voice/use_cases/handle_voice_confirmation.py` - Use case обработки подтверждения

#### Infrastructure Layer
- `src/infrastructure/config/settings.py` - Настройки конфигурации Voice/STT
- `src/infrastructure/voice/whisper_adapter.py` - Адаптер Whisper STT
- `src/infrastructure/voice/redis_store.py` - Хранилище команд Redis
- `src/infrastructure/voice/butler_gateway_impl.py` - Реализация gateway Butler
- `src/infrastructure/voice/confirmation_gateway_impl.py` - Gateway подтверждения (устарел)
- `src/infrastructure/voice/factory.py` - Фабрика use cases

#### Presentation Layer
- `src/presentation/bot/butler_bot.py` - Интеграция voice handler
- `src/presentation/bot/handlers/voice_handler.py` - Обработчик голосовых сообщений

#### Docker Infrastructure
- `docker/whisper-server/Dockerfile` - Docker образ Whisper STT
- `docker/whisper-server/server.py` - FastAPI сервер Whisper STT
- `docker/whisper-server/requirements.txt` - Python зависимости
- `docker-compose.butler.yml` - Конфигурация сервиса Whisper STT

## Тестирование
Для тестирования голосовых команд:
1. Запустите сервисы: `docker compose -f docker-compose.butler.yml up -d whisper-stt butler-bot`
2. Дождитесь загрузки модели Whisper (проверьте эндпоинт `/health`)
3. Отправьте голосовое сообщение в Telegram бот
4. Бот должен транскрибировать и выполнить команду автоматически

## Примечания
- **Немедленное выполнение**: Команды выполняются автоматически без подтверждения пользователя для лучшего UX
- **Устаревшие функции**: Поток подтверждения с кнопками устарел, но код остаётся для совместимости
- **Требуется GPU**: Сервер Whisper STT требует GPU (CUDA) для приемлемой производительности
- **Требуется Redis**: Голосовые команды требуют Redis для временного хранения команд
