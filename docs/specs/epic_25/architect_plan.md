# Epic 25 · Architect Plan – Personalised Butler

## 1. Summary
- Scope derived from `docs/specs/epic_25/epic_25.md` (Day 25).
- Goal: add user profile + memory + personalised reply pipeline (“Alfred-style дворецкий”) for Telegram bot (text + voice).
- Constraints: run on shared/local infra only, reuse Butler orchestrator, Russian persona baseline.

## 2. Architecture Overview
```
Telegram Update (text / voice→STT)
        ↓ (Presentation)
PersonalizedMessageHandler
        ↓ (Application)
PersonalizedReplyUseCase
   ┌────────┴─────────┐
UserProfileRepository  UserMemoryRepository
        ↓                     ↓
   UserProfile            RecentMemorySlice
        ↓                     ↓
   PersonalizationService → PromptAssembler
        ↓
Local LLM Client (existing adapter)
        ↓
Reply + Memory write-back
        ↓
Telegram Response
```

## 3. Domain Layer (`src/domain/personalization/`)
- **Value Objects**
  - `UserProfile`: `user_id`, `language`, `tone`, `persona`, `preferences` (topics, style).
  - `UserMemoryEvent`: `event_id`, `user_id`, `role (user|bot)`, `text`, `created_at`.
  - `MemorySlice`: `events: List[UserMemoryEvent]`, `summary`.
- **Interfaces**
  - `UserProfileRepository`: `get(user_id) -> Optional[UserProfile]`, `save(profile)`, `reset(user_id)`.
  - `UserMemoryRepository`: `list_recent(user_id, limit)`, `append(events)`, `compress(user_id)`.
  - `PersonalizationService`: `build_prompt(profile, memory_slice, new_message) -> PersonalizedPrompt`.
    - `PersonalizedPrompt`: persona instructions + memory context + new text.
- **Policies**
  - Default persona: Alfred-style butler (snarky yet helpful, Russian).
  - Memory cap per user (e.g., 50 events) before compression.

## 4. Application Layer (`src/application/personalization/`)
- **Use Case `PersonalizedReplyUseCase`**
  1. Ensure profile exists (create default if missing).
  2. Load latest memory slice (N events, summary).
  3. Call `PersonalizationService` to craft prompt.
  4. Invoke local LLM (existing `LLMClient`).
  5. Persist user/bot messages as memory events.
  6. Return response text for Telegram.
- **Use Case `ResetPersonalizationUseCase`** (invoked by admin tooling/CLI): delete profile & memory.
- **Gateways**
  - `ButlerGateway` reused for orchestrator/integration tests.
  - `VoiceGateway` (from Day 24) feeds transcription text into personalized use case.

## 5. Infrastructure Layer
- **Repositories (Mongo)**
  - Collections:
    - `user_profiles`: indexed by `user_id`.
    - `user_memory`: compound index (`user_id`, `created_at`), TTL for archived summaries.
  - Use shared Mongo config from EP24 (DI-based clients).
- **Memory Compression**
  - Cron/worker (optional) or inline `compress()` after threshold: summarise old events via local LLM summarizer (map-reduce logic from Cluster D).
- **Metrics**
  - `user_profile_reads_total`, `user_profile_writes_total`.
  - `user_memory_events_total{role}`, `user_memory_compressions_total`.
  - `personalized_requests_total`, `personalized_prompt_tokens_total`.
- **Logging**
  - Structured logs with `user_id`, `persona_id`, `memory_events_used`.

## 6. Presentation Layer (Telegram Bot)
- **Handlers**
  - Text: `PersonalizedMessageHandler` intercepts standard text messages → personalised use case.
  - Voice: reuse Day 24 pipeline (voice→text) then pass text to personalized use case.
  - No new public profile commands in Day 25; personalisation is automatic for all users.
- **Feature Flag**
  - Default ON; add env var (e.g., `PERSONALIZATION_ENABLED`) for quick disable.

## 7. Data & Prompt Strategy
- **Profile template**
  ```
  Persona: Alfred-style дворецкий (вежливый, ироничный, заботливый).
  Language: ru-RU.
  Tone: witty, respectful.
  Preferences: ${profile.preferences}
  ```
- **Memory formatting**
  ```
  Recent interactions:
  - User: ...
  - Butler: ...
  Summary: ...
  New message: ${latest_text}
  ```
- Ensure total token count < local LLM limit (<=4k). Apply summarizer when events > threshold.

## 8. Observability & Testing
- **Observability**
  - Extend `/metrics` endpoints to expose new counters/gauges.
  - Loki alerts for high personalized error rate, memory compression failures.
- **Testing**
  - Unit tests: profile/memory repositories (with Mongo fixtures), personalization service prompt assembly, use cases.
  - Integration tests: Telegram text → personalized reply path, voice → transcription → personalized reply.
  - Characterization tests to ensure existing digest flows unaffected.

## 9. Deliverables for Tech Lead
1. Update `docs/specs/epic_25/backlog.md` with TL stages (profile repo, memory repo, personalization use case, Telegram integration, observability/docs).
2. Create/extend acceptance matrix referencing new metrics/tests/docs.
3. Align with EP24 voice pipeline to confirm interface compatibility.

## 10. Open Questions & Decisions
1. **Memory compression cadence** – ✅ Решение: гибридный подход
   - Inline safeguard: после каждого ответа проверяем лимит (например, >50 событий) и при превышении сразу сжимаем (summary + последние N).  
   - Фоновый worker/cron: периодически оптимизирует память, обновляет summary, убирает старые записи. Worker работает через тот же `UserMemoryRepository.compress(user_id)`.
2. **Profile customization exposure** – ✅ Для Day 25 достаточно внутреннего CLI/скрипта (`scripts/tools/profile_admin.py`). Публичных команд настройки/сброса профиля нет.
3. **LLM prompt size** – ✅ Qwen-7B локально имеет окно 4 096 токенов; держим персонализированный prompt ≤ ~2 000 токенов (persona ≤200, memory slice ≤800, summary ≤300, новое сообщение ≤200, остальной запас для служебного текста).

Эти решения зафиксировать в TL-00 и acceptance matrix перед стартом разработки.

