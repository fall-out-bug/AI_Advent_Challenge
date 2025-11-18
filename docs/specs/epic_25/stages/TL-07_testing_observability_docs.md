# Stage TL-07: Testing, Observability & Documentation

**Epic**: EP25 - Personalised Butler  
**Stage**: TL-07  
**Duration**: 1.5 days  
**Owner**: Tech Lead + QA  
**Dependencies**: TL-06  
**Status**: Pending

---

## Goal

Expand test coverage, add Prometheus alerts, and complete all documentation for Epic 25.

---

## Objectives

1. Expand E2E tests for full personalization flow
2. Add Prometheus alerts for personalization
3. Update project documentation (README, challenge_days.md)
4. Create user guide for personalization
5. Update operational metrics documentation

---

## File Structure

```
tests/e2e/personalization/
├── __init__.py
├── test_text_flow.py              # E2E text message flow
├── test_voice_flow.py             # E2E voice message flow
└── test_memory_compression.py     # E2E compression flow

config/prometheus/alerts/
└── personalization.yml            # Prometheus alerts

docs/guides/
└── personalized_butler_user_guide.md  # User-facing guide

docs/operational/
└── metrics.md                     # Updated with personalization metrics

docs/specs/epic_25/
└── FINAL_REPORT.md                # Epic completion report
```

---

## Implementation Details

### 1. E2E Tests

**File**: `tests/e2e/personalization/test_text_flow.py`

**Requirements**:
- Full integration test with real services (testcontainers)
- Test text message → personalized reply → memory stored
- Verify Alfred persona in replies
- Check memory persistence

**Implementation**:

```python
"""E2E tests for text personalization flow."""

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from src.application.personalization.dtos import PersonalizedReplyInput
from src.infrastructure.personalization.factory import (
    create_personalized_use_cases
)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_text_personalized_reply_flow(
    mongo_client,
    llm_client,
    settings
):
    """Test full text message personalization flow.
    
    Purpose:
        Verify that:
        1. User profile is auto-created with Alfred persona
        2. LLM generates reply with persona
        3. Interaction is saved to memory
        4. Subsequent request uses memory context
    """
    # Create use cases
    reply_use_case, _ = create_personalized_use_cases(
        settings, mongo_client, llm_client
    )
    
    user_id = "e2e_test_text_123"
    
    # First interaction
    input_data1 = PersonalizedReplyInput(
        user_id=user_id,
        text="Hello, who are you?",
        source="text"
    )
    
    output1 = await reply_use_case.execute(input_data1)
    
    # Verify reply has Alfred characteristics
    assert output1.used_persona is True
    assert output1.reply
    # Check for Alfred-style markers (case-insensitive)
    reply_lower = output1.reply.lower()
    has_alfred_markers = any([
        "сэр" in reply_lower,
        "alfred" in reply_lower,
        "дворецкий" in reply_lower,
    ])
    assert has_alfred_markers or len(output1.reply) > 20  # Reasonable reply
    
    # Verify memory was saved
    assert output1.memory_events_used == 0  # First interaction
    
    # Second interaction (should use memory from first)
    input_data2 = PersonalizedReplyInput(
        user_id=user_id,
        text="What did I just ask you?",
        source="text"
    )
    
    output2 = await reply_use_case.execute(input_data2)
    
    # Verify memory context used
    assert output2.used_persona is True
    assert output2.memory_events_used >= 2  # User + assistant from first interaction
    
    # Verify profile exists in MongoDB
    db = mongo_client[settings.db_name]
    profile = await db.user_profiles.find_one({"user_id": user_id})
    
    assert profile is not None
    assert profile["persona"] == "Alfred-style дворецкий"
    assert profile["language"] == "ru"
    
    # Verify memory events exist
    event_count = await db.user_memory.count_documents({"user_id": user_id})
    assert event_count == 4  # 2 interactions × 2 events (user + assistant)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_personalization_disabled_fallback(
    mongo_client,
    llm_client,
    settings_with_personalization_disabled
):
    """Test that system works when personalization is disabled."""
    # ... test implementation ...
```

**File**: `tests/e2e/personalization/test_voice_flow.py`

```python
"""E2E tests for voice personalization flow."""

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_voice_personalized_reply_flow(
    mongo_client,
    llm_client,
    whisper_client,
    settings
):
    """Test full voice message personalization flow.
    
    Purpose:
        Verify that:
        1. Voice is transcribed via Whisper STT
        2. Transcription is routed to personalized reply
        3. Memory is saved with source="voice"
    """
    # ... test implementation ...
```

**File**: `tests/e2e/personalization/test_memory_compression.py`

```python
"""E2E tests for memory compression."""

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_memory_compression_trigger(
    mongo_client,
    llm_client,
    settings
):
    """Test that memory compression triggers at threshold.
    
    Purpose:
        Verify that:
        1. >50 events triggers compression
        2. Compression creates summary
        3. Old events are deleted, last 20 kept
        4. Profile is updated with summary
    """
    from src.infrastructure.personalization.factory import (
        create_personalized_use_cases
    )
    from src.application.personalization.dtos import PersonalizedReplyInput
    
    reply_use_case, _ = create_personalized_use_cases(
        settings, mongo_client, llm_client
    )
    
    user_id = "e2e_test_compression_123"
    
    # Send 51 messages to trigger compression (cap is 50)
    for i in range(51):
        input_data = PersonalizedReplyInput(
            user_id=user_id,
            text=f"Message {i}",
            source="text"
        )
        output = await reply_use_case.execute(input_data)
        
        # Last message should trigger compression
        if i == 50:
            assert output.compressed is True
    
    # Verify compression result
    db = mongo_client[settings.db_name]
    
    # Check event count (should be ≤20 after compression)
    event_count = await db.user_memory.count_documents({"user_id": user_id})
    assert event_count <= 20
    
    # Check profile has summary
    profile = await db.user_profiles.find_one({"user_id": user_id})
    assert profile["memory_summary"] is not None
    assert len(profile["memory_summary"]) > 0
```

---

### 2. Prometheus Alerts

**File**: `config/prometheus/alerts/personalization.yml`

**Requirements**:
- Alerts for high error rate
- Alerts for compression failures
- Alerts for memory growth

**Implementation**:

```yaml
groups:
  - name: personalization
    interval: 30s
    rules:
      # Alert: High error rate in personalized requests
      - alert: PersonalizationHighErrorRate
        expr: |
          rate(personalized_requests_total{status="error"}[5m]) 
          / 
          rate(personalized_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
          component: personalization
        annotations:
          summary: "High error rate in personalized requests (>10%)"
          description: "{{ $value | humanizePercentage }} of personalized requests are failing in the last 5 minutes"
          runbook: "Check logs for personalized_reply_use_case, verify LLM and MongoDB connectivity"

      # Alert: Memory compression failures
      - alert: MemoryCompressionFailures
        expr: rate(personalized_memory_compressions_total{status="error"}[5m]) > 5
        for: 5m
        labels:
          severity: critical
          component: personalization
        annotations:
          summary: "Memory compression failures (>5 in 5min)"
          description: "Memory compression is failing at {{ $value }} errors per second"
          runbook: "Check logs for _compress_memory, verify LLM summarization working"

      # Alert: High profile read latency
      - alert: ProfileReadHighLatency
        expr: |
          histogram_quantile(0.95, 
            rate(user_profile_read_duration_seconds_bucket[5m])
          ) > 1.0
        for: 10m
        labels:
          severity: warning
          component: personalization
        annotations:
          summary: "High profile read latency (p95 >1s)"
          description: "95th percentile profile read latency is {{ $value }}s"
          runbook: "Check MongoDB performance, verify indexes exist"

      # Alert: Memory event count growth
      - alert: MemoryEventCountHigh
        expr: |
          sum by (user_id) (
            increase(user_memory_events_total[1h])
          ) > 200
        for: 15m
        labels:
          severity: info
          component: personalization
        annotations:
          summary: "High memory event count for user (>200/hour)"
          description: "User {{ $labels.user_id }} has {{ $value }} events in last hour"
          runbook: "Investigate user activity, possible spam or bot"

      # Alert: Prompt token limit exceeded frequently
      - alert: PromptTokenLimitExceeded
        expr: |
          rate(personalized_prompt_truncations_total[5m]) > 10
        for: 10m
        labels:
          severity: warning
          component: personalization
        annotations:
          summary: "Frequent prompt truncations (>10/min)"
          description: "Prompts are being truncated {{ $value }} times per minute"
          runbook: "Review prompt assembly logic, consider reducing context size"
```

---

### 3. User Guide

**File**: `docs/guides/personalized_butler_user_guide.md`

```markdown
# Персонализированный Butler — Руководство пользователя

## Что такое персонализированный Butler?

Butler теперь помнит вас и ваши предыдущие разговоры! Бот использует персону "Alfred-style дворецкий" (вежливый, ироничный, заботливый, как Alfred из Batman).

## Как это работает

### Автоматическая персонализация

- **Включено автоматически**: Персонализация работает для всех ваших сообщений
- **Память**: Butler помнит последние 50 сообщений
- **Persona**: Ответы в стиле Alfred (английский юмор, русский язык)

### Примеры взаимодействия

**Обычный запрос**:
```
You: Привет!
Butler: Добрый день, сэр. Надеюсь, день проходит без излишней драмы? Чем могу быть полезен?
```

**С контекстом**:
```
You: Расскажи про Python
Butler: (подробный ответ про Python)

You: А какие есть библиотеки?
Butler: Раз уж мы говорим о Python, позвольте рассказать о наиболее популярных библиотеках...
```

### Голосовые сообщения

Butler поддерживает голосовые сообщения:

1. Отправьте голосовое сообщение
2. Butler распознает речь (Whisper STT)
3. Отвечает текстом в стиле Alfred

## Память

### Как Butler запоминает

- **50 последних сообщений**: Butler помнит ваши последние разговоры
- **Автоматическое сжатие**: Старые сообщения сжимаются в краткую сводку
- **90 дней**: История автоматически удаляется через 90 дней

### Сброс памяти

Если хотите начать заново, обратитесь к администратору для сброса профиля.

## Конфиденциальность

- **Локальное хранение**: Все данные хранятся локально в MongoDB (не отправляются в external SaaS)
- **Автоудаление**: История автоматически удаляется через 90 дней
- **Безопасность**: Доступ только у вас и администраторов системы

## Типичные вопросы

### Почему Butler отвечает в стиле Alfred?

Это персона по умолчанию для всех пользователей. Она создана для того, чтобы делать взаимодействие более живым и интересным, сохраняя при этом профессионализм.

### Можно ли изменить персону?

В текущей версии персона фиксирована. Возможность настройки появится в будущих обновлениях.

### Что делать, если Butler ведет себя странно?

Обратитесь к администратору для сброса вашего профиля. Это удалит всю историю и вернет настройки по умолчанию.

### Работает ли персонализация с командами?

Да! Персонализация работает со всеми текстовыми и голосовыми сообщениями, включая команды для работы с дайджестами, домашними заданиями и т.д.

## Технические детали

### Модель

- **LLM**: Qwen-7B (локальная модель)
- **STT**: Whisper base model (для голосовых сообщений)
- **Язык**: Optimized для русского языка

### Ограничения

- **Память**: Максимум 50 сообщений (старые сжимаются)
- **Длина сообщения**: Ограничения Telegram (до 4096 символов)
- **Голос**: Только текстовые ответы (без синтеза речи)

## Поддержка

По вопросам и проблемам обращайтесь к администраторам системы.

---

**Версия**: 1.0  
**Дата обновления**: 2025-11-18
```

---

### 4. Project Documentation Updates

**File**: `README.md` (add section)

```markdown
## Personalization

Butler includes personalized interactions with "Alfred-style дворецкий" persona:

- **Memory**: Remembers last 50 messages per user
- **Persona**: Alfred Pennyworth style (witty, caring, respectful)
- **Voice Support**: Works with voice messages via Whisper STT
- **Privacy**: All data stored locally (no external SaaS)

See [Personalized Butler User Guide](docs/guides/personalized_butler_user_guide.md) for details.
```

**File**: `docs/challenge_days.md` (add section)

```markdown
### День 25: Персонализированный Butler

**Цель**: Превратить Butler в персонализированного помощника с памятью и персоной.

**Реализация**:
- User profiles (persona, language, tone)
- Memory management (last 50 events, auto-compression)
- "Alfred-style дворецкий" persona (English humor, Russian language)
- Voice integration (STT → personalized reply)
- Feature flag для постепенного rollout

**Технологии**:
- MongoDB (profiles + memory)
- Local LLM (Qwen-7B для генерации и summarization)
- Whisper STT (voice transcription)
- Prometheus (metrics + alerts)

**Результат**: Butler помнит пользователей и отвечает в стиле Alfred.

**Документация**: `docs/specs/epic_25/`
```

---

### 5. Operational Metrics Documentation

**File**: `docs/operational/metrics.md` (add section)

```markdown
## Personalization Metrics

### Profile Metrics

- `user_profile_reads_total` — Total profile reads
- `user_profile_writes_total` — Total profile writes

### Memory Metrics

- `user_memory_events_total{role}` — Total memory events by role (user/assistant)
- `user_memory_compressions_total` — Total memory compressions

### Request Metrics

- `personalized_requests_total{source,status}` — Personalized requests by source and status
- `personalized_prompt_tokens_total` — Prompt token count (histogram)

### Compression Metrics

- `user_memory_compression_duration_seconds` — Compression duration (histogram)

### Alerts

- `PersonalizationHighErrorRate` — >10% error rate in 5 minutes
- `MemoryCompressionFailures` — >5 compression failures in 5 minutes
- `ProfileReadHighLatency` — p95 profile read >1s
- `MemoryEventCountHigh` — >200 events/hour for user
- `PromptTokenLimitExceeded` — >10 truncations/minute
```

---

## Testing Requirements

### E2E Test Coverage

- **Text Flow**: 100%
  - Profile auto-creation
  - Memory persistence
  - Context usage
  
- **Voice Flow**: 100%
  - STT integration
  - Personalized reply
  - Memory saving

- **Compression**: 100%
  - Trigger at threshold
  - Summary generation
  - Event deletion

### Test Execution

```bash
# E2E tests (requires testcontainers)
pytest tests/e2e/personalization/ -v -m e2e

# Full test suite
pytest tests/ -v --cov=src --cov-report=term-missing

# Check coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Acceptance Criteria

- [ ] E2E tests for text/voice/compression flows
- [ ] Prometheus alerts configured and tested
- [ ] User guide complete and reviewed
- [ ] Project documentation updated (README, challenge_days.md)
- [ ] Operational metrics documented
- [ ] Epic completion report written
- [ ] All tests passing (unit + integration + E2E)
- [ ] Coverage ≥80% overall

---

## Dependencies

- **Upstream**: TL-06 (admin tools)
- **Downstream**: TL-08 (background worker, optional)

---

## Deliverables

- [ ] `tests/e2e/personalization/*.py`
- [ ] `config/prometheus/alerts/personalization.yml`
- [ ] `docs/guides/personalized_butler_user_guide.md`
- [ ] Updated `README.md`
- [ ] Updated `docs/challenge_days.md`
- [ ] Updated `docs/operational/metrics.md`
- [ ] `docs/specs/epic_25/FINAL_REPORT.md`

---

## Next Steps

After completion:
1. Full test suite run (unit + integration + E2E)
2. Documentation review with stakeholders
3. Metrics/alerts review in Prometheus
4. Epic sign-off
5. Optional: Begin TL-08 (Background Worker)

---

**Status**: Pending  
**Estimated Effort**: 1.5 days  
**Priority**: High

