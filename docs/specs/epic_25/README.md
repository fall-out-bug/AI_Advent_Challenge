# Epic 25 · Personalised Butler ("Alfred-style дворецкий")

## Overview
Epic 25 transforms Butler into a personalised assistant that remembers users, their preferences, and past interactions. The bot responds in the "Alfred-style дворецкий" persona (snarky but caring, witty, respectful, Russian language).

## Key Features
- ✅ **User Profiles** with persona, language, tone preferences
- ✅ **Memory Management** with automatic compression (last 50 events)
- ✅ **"Alfred-style дворецкий" Persona** (English humour, Russian language)
- ✅ **Text & Voice Integration** (reuses EP24 voice pipeline)
- ✅ **Local Infrastructure** (Mongo, local LLM only)
- ✅ **Always-On Personalisation** (automatic for all messages)

## Documentation
- [Tech Lead Plan](./tech_lead_plan.md) - Detailed implementation plan with stages
- [Acceptance Matrix](./acceptance_matrix.md) - Acceptance criteria and evidence
- [Developer Handoff](./dev_handoff.md) - Developer guide with code examples
- [Architecture Plan](./architect_plan.md) - Architecture overview and decisions
- [Backlog](./backlog.md) - Task breakdown

## Quick Reference

### Core Persona: "Alfred-style дворецкий"
- **Character**: Alfred Pennyworth from Batman
- **Traits**: Polite, ironic, caring, witty, respectful
- **Style**: English humour, Russian language
- **Tone**: Helpful and informative with light sarcasm

**Example interactions**:
- User: "Привет!"
- Butler: "Добрый день, сэр. Надеюсь, день проходит без излишней драмы? Чем могу быть полезен?"

### Architecture Layers

#### Domain Layer
- **Value Objects** (`src/domain/personalization/`):
  - `UserProfile`: user_id, language, persona, tone, preferred_topics, memory_summary
  - `UserMemoryEvent`: event_id, user_id, role (user/assistant), content, created_at
  - `MemorySlice`: events, summary, total_events
  - `PersonalizedPrompt`: persona_section, memory_context, new_message, full_prompt
- **Protocols** (`src/domain/interfaces/personalization.py`):
  - `UserProfileRepository`: get, save, reset
  - `UserMemoryRepository`: append_events, get_recent_events, compress, count_events
  - `PersonalizationService`: load_profile, build_personalized_prompt

#### Application Layer
- **Use Cases** (`src/application/personalization/use_cases/`):
  - `PersonalizedReplyUseCase`: Load profile+memory → build prompt → call LLM → save interaction
  - `ResetPersonalizationUseCase`: Clear profile and memory
- **Service** (`src/application/personalization/`):
  - `PersonalizationServiceImpl`: Profile loading, prompt assembly, token estimation
- **Templates** (`src/application/personalization/templates.py`):
  - Persona template, memory context template, full prompt template

#### Infrastructure Layer
- **Repositories** (`src/infrastructure/personalization/`):
  - `MongoUserProfileRepository`: Mongo-backed profile storage
  - `MongoUserMemoryRepository`: Mongo-backed memory storage with compression
- **Factory** (`src/infrastructure/personalization/factory.py`):
  - `create_personalized_use_cases()`: DI for use cases

#### Presentation Layer
- **Handlers** (`src/presentation/bot/handlers/`):
  - Updated `message_handler.py`: Route text messages through personalised use case
  - Updated `voice_handler.py`: Route STT output through personalised use case
- **Admin Tools** (`scripts/tools/profile_admin.py`):
  - CLI for profile management (list, show, reset, update)

### Data Flow

1. **User sends message** (text or voice) → Telegram Bot
2. **Handler** extracts user_id and message text
3. **PersonalizedReplyUseCase**:
   - Load `UserProfile` (auto-create with Alfred persona if missing)
   - Load recent `UserMemoryEvent`s (last 20 events)
   - Check event count: if >50 → compress inline
   - Build `PersonalizedPrompt` (persona + memory + new message)
   - Call local LLM with prompt
   - Save user/assistant events to memory
4. **Send personalized reply** to user via Telegram

### Mongo Collections

#### `user_profiles`
```json
{
  "_id": ObjectId,
  "user_id": "123456789",
  "language": "ru",
  "persona": "Alfred-style дворецкий",
  "tone": "witty",
  "preferred_topics": [],
  "memory_summary": "User has been asking about...",
  "created_at": ISODate,
  "updated_at": ISODate
}
```
**Index**: `{"user_id": 1}` (unique)

#### `user_memory`
```json
{
  "_id": ObjectId,
  "event_id": UUID,
  "user_id": "123456789",
  "role": "user",  // "user" or "assistant"
  "content": "Message text",
  "created_at": ISODate,
  "tags": []
}
```
**Indexes**:
- `{"user_id": 1, "created_at": -1}` (compound for efficient queries)
- `{"created_at": 1, expireAfterSeconds: 7776000}` (TTL: 90 days)

### Configuration

**Environment Variables** (in `docker-compose.butler.yml`):
```bash
# Personalisation
PERSONALIZATION_ENABLED=true  # Default: true (set to false to disable)

# Mongo (shared from EP24)
MONGODB_URL=mongodb://admin:password@shared-mongo:27017/butler?authSource=admin

# LLM (shared)
LLM_API_URL=http://llm-api:8000
```

### Commands

**Admin CLI**:
```bash
# List all profiles
python scripts/tools/profile_admin.py list

# Show profile and memory stats
python scripts/tools/profile_admin.py show <user_id>

# Reset profile and memory
python scripts/tools/profile_admin.py reset <user_id>

# Update profile
python scripts/tools/profile_admin.py update <user_id> --persona "Custom persona" --tone witty
```

### Metrics

**Prometheus Metrics**:
- `user_profile_reads_total` — Total user profile reads
- `user_profile_writes_total` — Total user profile writes
- `user_memory_events_total{role}` — Total memory events appended (by role)
- `user_memory_compressions_total` — Total memory compressions
- `personalized_requests_total{source,status}` — Total personalized requests (by source and status)
- `personalized_prompt_tokens_total` — Personalized prompt token count (histogram)

**Prometheus Alerts**:
- `PersonalizationHighErrorRate` — Alert if error rate >10%
- `MemoryCompressionFailures` — Alert if >5 failures in 5min

### Memory Management

**Memory Cap**: 50 events per user

**Compression Trigger**: Automatically triggered when event count >50

**Compression Process**:
1. Load all events for user
2. Summarize via local LLM (max 300 tokens)
3. Delete old events, keep last 20
4. Update profile with summary

**Auto-Cleanup**: TTL index (90 days) for archived events

### Prompt Strategy

**Prompt Structure**:
```
[Persona Section]
Ты — Alfred-style дворецкий. Твой тон: witty. Язык ответа: ru.
Instructions: (English humour, Russian language, helpful with light sarcasm)

[Memory Context]
Previous interactions:
- User: ...
- Butler: ...
Summary: (compressed history)

[New Message]
User: {new_message}
Butler:
```

**Token Limits**:
- Qwen-7B window: 4096 tokens
- Personalized prompt target: ≤2000 tokens
  - Persona section: ≤200 tokens
  - Memory context: ≤800 tokens
  - Summary: ≤300 tokens
  - New message: ≤200 tokens
  - Buffer: ≤500 tokens

**Truncation**: If prompt >2000 tokens → keep summary + last 5 events

## Status
**Status**: ✅ **COMPLETED & DEPLOYED**
**Completion Date**: 2025-11-18
**Tech Lead**: Approved and signed off

## Implementation Stages

| Stage | Objective | Duration | Status |
| --- | --- | --- | --- |
| TL-00 | Scope confirmation & decisions | 1d | ✅ Complete |
| TL-01 | Domain models & interfaces | 1.5d | ✅ Complete |
| TL-02 | Infrastructure repositories (Mongo) | 2d | ✅ Complete |
| TL-03 | Personalisation service & prompt assembly | 1.5d | ✅ Complete |
| TL-04 | Personalised reply use case | 2d | ✅ Complete |
| TL-05 | Telegram bot integration | 2d | ✅ Complete |
| TL-06 | Admin tools (CLI only) | 1d | ✅ Complete |
| TL-07 | Testing, observability, docs & rollout | 1.5d | ✅ Complete |
| Task 16 | Interest extraction & profile enrichment | 1d | ✅ Complete |

**Total Duration**: ~12.5 days (including Task 16)

## Testing Strategy

### Unit Tests
- Value objects (validation, factories, serialization)
- Prompt assembly (token estimation, truncation)
- Use cases (mocked repos/LLM)
- Repositories (with fakemongo)

### Integration Tests
- Mongo repositories (with testcontainers)
- Telegram handlers (mock bot API)
- E2E: Text → personalized reply → memory stored
- E2E: Voice → STT → personalized reply → memory stored
- Memory compression (>50 events → compress)

### Manual Tests
- Send text message → verify Alfred-style reply
- Send voice message → verify STT → personalized reply
- Send 51 messages → verify compression
- CLI tools → verify CRUD operations

## Dependencies
- **EP23**: Observability stack (Prometheus, Loki)
- **EP24**: Voice integration (STT, Redis)
- **Shared Infra**: MongoDB, local LLM (Qwen-7B)

## Known Limitations
- **Memory cap**: 50 events per user (older events compressed)
- **Persona customization**: Internal CLI only (no public commands in MVP)
- **Language support**: Optimized for Russian (extensible to other languages)
- **LLM prompt size**: Limited to 2000 tokens (truncation applied if exceeded)

## Future Improvements
- Multi-language support (English, etc.)
- Public persona customization commands
- Background worker for periodic memory optimization
- Cross-device identity management
- Deeper MCP/homework integration

## References
- **Challenge Days**: `docs/challenge_days.md#день-25-персонализированный-батлер`
- **User Guide**: `docs/user_guides/personalized_butler.md`
- **Metrics Docs**: `docs/operational/metrics.md`
- **Architecture**: `docs/specs/epic_25/architect_plan.md`

---

**README Version**: 2.0
**Last Updated**: 2025-11-18
**Status**: ✅ Epic 25 Complete - All stages delivered, tested, and deployed
