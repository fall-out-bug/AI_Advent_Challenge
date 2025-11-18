# Epic 25 · Tech Lead Implementation Plan
_Day 25 · Personalised Butler ("Alfred-style дворецкий")_

## 1. Metadata & Inputs
| Field | Value |
| --- | --- |
| Epic | EP25 |
| Scope | Personalised assistant with user profiles, memory, and "Alfred-style дворецкий" persona |
| Tech Lead | cursor_tech_lead_v1 |
| Date | 2025-11-18 |
| Source Requirements | `docs/challenge_days.md#день-25-персонализированный-батлер`, `docs/specs/epic_25/epic_25.md` |
| Architecture Reference | `docs/specs/epic_25/architect_plan.md` |
| Dependencies | EP23 observability, EP24 voice integration, shared infra (Mongo/LLM) |

## 2. Objectives & Assumptions
- **Personalisation always on**: Text messages automatically go through personalised reply path; no opt-in needed.
- **Persona baseline**: "Alfred-style дворецкий" (snarky but caring, witty, respectful, Russian language).
- **Memory management**: Store recent interactions per user; compress older history when threshold exceeded (>50 events).
- **Local LLM only**: Use existing Qwen-7B API; no external SaaS.
- **Voice integration**: Reuse EP24 voice→text pipeline, then apply personalisation to transcribed text.
- **Observability**: Extend EP23 metrics stack with personalisation-specific counters.

## 3. Stage Overview
| Stage | Objective | Owner(s) | Duration (d) | Dependencies | Evidence |
| --- | --- | --- | --- | --- | --- |
| TL-00 | Scope confirmation & decisions | Tech Lead + Architect | 1 | — | Decisions log, updated backlog |
| TL-01 | Domain models & interfaces | Dev A | 1.5 | TL-00 | Value objects, protocols, unit tests |
| TL-02 | Infrastructure repositories (Mongo) | Dev B | 2 | TL-01 | Profile/memory repos, indexes, integration tests |
| TL-03 | Personalisation service & prompt assembly | Dev A | 1.5 | TL-01, TL-02 | Service implementation, prompt builder, unit tests |
| TL-04 | Personalised reply use case | Dev A + Dev B | 2 | TL-03 | Use case code, integration with LLM client |
| TL-05 | Telegram bot integration | Dev C | 2 | TL-04 | Handler updates, voice path integration, manual tests |
| TL-06 | Admin tooling (CLI only) | Dev C | 1 | TL-05 | `profile_admin.py` tool |
| TL-07 | Testing, observability, docs & rollout | QA + Tech Lead | 1.5 | TL-06 | Test logs, metrics, doc updates |
| TL-08 | Background memory compression worker | Dev B + DevOps | 2 | TL-04 | Worker script, scheduler config, monitoring |

**Parallelisation note**: TL-01 and TL-02 can overlap (repos use domain contracts); TL-03 waits for TL-02 data access.

## 4. Stage Details

### TL-00 · Scope Confirmation
**Decisions**:
- **Persona**: "Alfred-style дворецкий" — вежливый, ироничный, заботливый (English humour, Russian language). Фиксированная baseline версия в коде, кастомизация через админ-скрипт (не через публичные команды).
- **Memory cap**: Хранить последние 50 событий per user; при превышении — inline compression (summary + last N events). Опциональный фоновый worker для периодической оптимизации (not blocking MVP).
- **LLM prompt size**: Qwen-7B window 4096 tokens; персонализированный prompt ≤ 2000 tokens (persona ≤200, memory slice ≤800, summary ≤300, new message ≤200, buffer ≤500).
- **Profile exposure**: MVP — только внутренний CLI (`scripts/tools/profile_admin.py`). Публичных команд настройки/сброса профиля нет.
- **Voice integration**: После STT транскрипции (EP24) текст направляется в `PersonalizedReplyUseCase` вместо прямого вызова Butler. Ответ остаётся текстовым (TTS out of scope).
- **Personalisation mode**: Always-on для всех текстовых сообщений; feature flag `PERSONALIZATION_ENABLED` (default True) для аварийного отключения.

**Deliverables**:
- `docs/specs/epic_25/backlog.md` updated with TL25-* tasks.
- Worklog entry capturing decisions.

### TL-01 · Domain Models & Interfaces
**Tasks**:
1. Define `UserProfile` value object (`src/domain/personalization/user_profile.py`):
   - Fields: `user_id: str`, `language: str`, `persona: str`, `tone: str`, `preferred_topics: List[str]`, `created_at: datetime`, `updated_at: datetime`.
   - Default factory: `create_default_profile(user_id) -> UserProfile` with "Alfred-style дворецкий" persona, Russian language.
   - Validation: language in [ru, en], tone in [witty, formal, casual].
2. Define `UserMemoryEvent` value object (`src/domain/personalization/user_memory_event.py`):
   - Fields: `event_id: UUID`, `user_id: str`, `role: Literal["user", "assistant"]`, `content: str`, `created_at: datetime`, `tags: List[str]` (optional).
   - Factory: `create_user_event(user_id, content) -> UserMemoryEvent`, `create_assistant_event(user_id, content) -> UserMemoryEvent`.
3. Define `MemorySlice` value object (`src/domain/personalization/memory_slice.py`):
   - Fields: `events: List[UserMemoryEvent]`, `summary: Optional[str]`, `total_events: int`.
   - Method: `to_prompt_context() -> str` (formats events for prompt injection).
4. Define `PersonalizedPrompt` value object (`src/domain/personalization/personalized_prompt.py`):
   - Fields: `persona_section: str`, `memory_context: str`, `new_message: str`, `full_prompt: str`.
   - Method: `estimate_tokens() -> int` (простая эвристика: len(full_prompt) / 4).
5. Define protocols (`src/domain/interfaces/personalization.py`):
   - `UserProfileRepository`:
     ```python
     class UserProfileRepository(Protocol):
         async def get(self, user_id: str) -> Optional[UserProfile]: ...
         async def save(self, profile: UserProfile) -> None: ...
         async def reset(self, user_id: str) -> None: ...
     ```
   - `UserMemoryRepository`:
     ```python
     class UserMemoryRepository(Protocol):
         async def append_events(self, events: List[UserMemoryEvent]) -> None: ...
         async def get_recent_events(self, user_id: str, limit: int) -> List[UserMemoryEvent]: ...
         async def compress(self, user_id: str, summary: str, keep_last_n: int) -> None: ...
         async def count_events(self, user_id: str) -> int: ...
     ```
   - `PersonalizationService`:
     ```python
     class PersonalizationService(Protocol):
         async def load_profile(self, user_id: str) -> UserProfile: ...
         async def build_personalized_prompt(
             self, profile: UserProfile, memory_slice: MemorySlice, new_message: str
         ) -> PersonalizedPrompt: ...
     ```

**Evidence**:
- Type-hinted modules with docstrings (100% coverage).
- Unit tests for value objects (validation, factories, `to_prompt_context()`).
- Protocols documented in `docs/specs/epic_25/architecture.md` (to be created).

### TL-02 · Infrastructure Repositories
**Tasks**:
1. Implement `MongoUserProfileRepository` (`src/infrastructure/personalization/profile_repository.py`):
   - Collection: `user_profiles` (shared Mongo from EP24).
   - Index: `{"user_id": 1}` (unique).
   - Methods:
     - `get(user_id)`: Find by `user_id`; if not found, create default profile via `UserProfile.create_default_profile(user_id)` and save.
     - `save(profile)`: Upsert by `user_id`.
     - `reset(user_id)`: Delete document, recreate default.
   - Error handling: Log Mongo exceptions, raise `RepositoryError`.
2. Implement `MongoUserMemoryRepository` (`src/infrastructure/personalization/memory_repository.py`):
   - Collection: `user_memory`.
   - Indexes:
     - `{"user_id": 1, "created_at": -1}` (compound for efficient recent queries).
     - Optional TTL index `{"created_at": 1, expireAfterSeconds: 7776000}` (90 days) for auto-cleanup.
   - Methods:
     - `append_events(events)`: Insert multiple documents.
     - `get_recent_events(user_id, limit)`: Query `user_id`, sort by `created_at` descending, limit N.
     - `compress(user_id, summary, keep_last_n)`:
       1. Count total events for user.
       2. If total > keep_last_n: keep last N events, delete older events.
       3. Store `summary` in a special "summary" event (role="system", content=summary) or in profile (tbd: decision — store in profile for simpler retrieval).
     - `count_events(user_id)`: Count documents for user.
   - **Decision (TL-00)**: Store summary in `UserProfile.memory_summary` field instead of separate event; update profile after compression.
3. Add Mongo migrations/indexes script (`scripts/migrations/add_personalization_indexes.py`):
   - Create indexes for `user_profiles` and `user_memory` collections.
   - Run as part of deployment (add to `make migrate` or Docker entrypoint).
4. Add metrics:
   - `user_profile_reads_total`, `user_profile_writes_total`.
   - `user_memory_events_total{role="user|assistant"}`.
   - `user_memory_compressions_total`.

**Evidence**:
- Repository integration tests with fakemongo/testcontainers.
- Metrics visible via `/metrics` endpoint.
- Indexes verified via `db.collection.getIndexes()` in test.

### TL-03 · Personalisation Service & Prompt Assembly
**Tasks**:
1. Implement `PersonalizationServiceImpl` (`src/application/personalization/personalization_service.py`):
   - Dependencies: `UserProfileRepository`, `UserMemoryRepository`.
   - Methods:
     - `load_profile(user_id)`:
       1. Call `profile_repo.get(user_id)` (creates default if missing).
       2. Return profile.
     - `build_personalized_prompt(profile, memory_slice, new_message)`:
       1. Build persona section from profile (persona + tone + language).
       2. Build memory context from `memory_slice.to_prompt_context()` + `memory_slice.summary` (if exists).
       3. Assemble full prompt: `persona_section + memory_context + "User: {new_message}\nButler:"`.
       4. Estimate tokens (simple heuristic: `len(full_prompt) / 4`).
       5. If estimated tokens > 2000: truncate memory context (keep summary + last 5 events).
       6. Return `PersonalizedPrompt`.
2. Implement `MemorySummarizerService` (optional, for background compression):
   - Method: `summarize_events(events: List[UserMemoryEvent]) -> str`.
   - Use local LLM client (existing `LLMClient`) with prompt:
     ```
     Summarise the following conversation history in Russian (max 300 tokens):
     {events}
     ```
   - For MVP: inline summarization in `PersonalizedReplyUseCase` when threshold exceeded (no separate worker).
3. Implement prompt templates (`src/application/personalization/templates.py`):
   - `PERSONA_TEMPLATE`:
     ```
     Ты — {persona}. Твой тон: {tone}. Язык ответа: {language}.
     Preferred topics: {preferred_topics}.

     Instructions:
     - Отвечай как Alfred из Batman (вежливый, ироничный, заботливый).
     - Используй английский юмор, но говори на русском.
     - Будь полезным и информативным, но добавляй лёгкую иронию.
     ```
   - `MEMORY_CONTEXT_TEMPLATE`:
     ```
     Previous interactions:
     {memory_events}

     Summary: {summary}
     ```
   - `FULL_PROMPT_TEMPLATE`:
     ```
     {persona_section}

     {memory_context}

     User: {new_message}
     Butler:
     ```

**Evidence**:
- Unit tests for `PersonalizationServiceImpl` (mock repos).
- Unit tests for prompt assembly (verify token estimation, truncation logic).
- Manual prompt inspection (log sample prompts for review).

### TL-04 · Personalised Reply Use Case
**Tasks**:
1. Implement `PersonalizedReplyUseCase` (`src/application/personalization/use_cases/personalized_reply.py`):
   - Input DTO: `PersonalizedReplyInput(user_id: str, text: str, source: Literal["text", "voice"] = "text")`.
   - Output DTO: `PersonalizedReplyOutput(reply: str, used_persona: bool, memory_events_used: int)`.
   - Dependencies: `PersonalizationService`, `UserMemoryRepository`, `LLMClient`.
   - Steps:
     1. Load profile via `personalization_service.load_profile(user_id)`.
     2. Get recent memory events: `memory_repo.get_recent_events(user_id, limit=20)`.
     3. Check event count: if `memory_repo.count_events(user_id) > 50`:
        - Compress inline: load all events, summarize via LLM, call `memory_repo.compress(user_id, summary, keep_last_n=20)`.
        - Update profile with summary: `profile.memory_summary = summary`, `profile_repo.save(profile)`.
     4. Build memory slice: `MemorySlice(events=recent_events, summary=profile.memory_summary)`.
     5. Build personalized prompt: `personalization_service.build_personalized_prompt(profile, memory_slice, text)`.
     6. Call LLM: `reply = await llm_client.generate(prompt.full_prompt)`.
     7. Append memory events:
        - User event: `UserMemoryEvent.create_user_event(user_id, text)`.
        - Assistant event: `UserMemoryEvent.create_assistant_event(user_id, reply)`.
        - `memory_repo.append_events([user_event, assistant_event])`.
     8. Return `PersonalizedReplyOutput(reply=reply, used_persona=True, memory_events_used=len(recent_events))`.
   - Error handling:
     - LLM failure: Log error, return fallback message ("Извините, временные технические проблемы. Попробуйте позже.").
     - Repo failure: Log error, skip memory persistence (graceful degradation).
2. Implement `ResetPersonalizationUseCase` (`src/application/personalization/use_cases/reset_personalization.py`):
   - Input: `user_id: str`.
   - Steps:
     1. `profile_repo.reset(user_id)`.
     2. `memory_repo.compress(user_id, summary="", keep_last_n=0)` (delete all events).
   - Return confirmation message.
3. Add structured logging:
   - Log `user_id`, `persona`, `memory_events_used`, `prompt_tokens`, `reply_length`.
4. Add metrics:
   - `personalized_requests_total{source="text|voice"}`.
   - `personalized_prompt_tokens_total` (histogram).
   - `personalized_memory_compressions_total`.

**Evidence**:
- Use case unit tests (mock repos, LLM client).
- Integration tests (use fake Mongo + real LLM if available, or mock).
- Metrics visible via `/metrics`.

### TL-05 · Telegram Bot Integration
**Tasks**:
1. Update text message handler (`src/presentation/bot/handlers/message_handler.py`):
   - **Before**: Route to `ButlerOrchestrator.handle_user_message()`.
   - **After**: Check if `PERSONALIZATION_ENABLED` (env var, default True):
     - If True: Route to `PersonalizedReplyUseCase`.
     - If False: Fallback to existing Butler flow.
   - Extract `user_id` from `message.from_user.id`.
   - Call `PersonalizedReplyUseCase(user_id=user_id, text=message.text, source="text")`.
   - Send reply via `message.answer(output.reply)`.
2. Update voice message handler (`src/presentation/bot/handlers/voice_handler.py`):
   - **Before**: After STT transcription, call Butler directly.
   - **After**: After STT transcription, call `PersonalizedReplyUseCase(user_id=user_id, text=transcription.text, source="voice")`.
   - Keep existing error handling and logging.
3. Add factory for use case injection (`src/infrastructure/personalization/factory.py`):
   - `create_personalized_use_cases(settings, mongo_client, llm_client) -> Tuple[PersonalizedReplyUseCase, ResetPersonalizationUseCase]`.
   - Wire up repos, services, use cases with DI.
4. Update bot initialization (`src/presentation/bot/butler_bot.py`):
   - Initialize personalization use cases in `setup()` method.
   - Pass to handlers via setup functions.
5. Add feature flag check:
   - `Settings.personalization_enabled: bool = True` (default).
   - If False: skip personalization, route directly to Butler (backward compatibility).

**Evidence**:
- Manual test: Send text message → verify personalized reply with Alfred persona.
- Manual test: Send voice message → verify STT → personalized reply.
- Integration test: Mock Telegram updates → verify use case invocation.

### TL-06 · Admin Tools Only (no public commands)
**Tasks**:
1. Implement admin CLI tool (`scripts/tools/profile_admin.py`) for internal use:
   - `list` — show all profiles (user_id, persona, memory stats).
   - `show <user_id>` — display profile + memory summary + event count.
   - `reset <user_id>` — call `ResetPersonalizationUseCase` (profile + memory clear).
   - `update <user_id> --persona ... --tone ... --language ...` — modify profile fields.
   - Use shared Mongo config; require admin env var (e.g. `PROFILE_ADMIN_API_KEY`) to avoid accidental usage.
2. Provide developer README snippet describing how to run CLI for support tasks.
3. `/profile` или другие user-facing команды остаются **out of scope** для Day 25 (persona используется автоматически, без публичных настроек).

**Evidence**:
- Manual test: `profile_admin.py reset <user_id>` → verify profile/memory cleared.
- Manual test: `profile_admin.py update <user_id> ...` → verify persona/tone updated in Mongo and reflected in replies.

### TL-07 · Testing, Observability & Docs
**Tasks**:
1. Expand integration tests:
   - End-to-end: Telegram text message → personalized reply → memory stored.
   - End-to-end: Voice message → STT → personalized reply → memory stored.
   - Memory compression: Send 51 messages → verify compression triggered.
2. Add Prometheus alerts (`config/prometheus/alerts/personalization.yml`):
   - `PersonalizationHighErrorRate`: Alert if `personalized_requests_total{status="error"}` > 10% of total requests.
   - `MemoryCompressionFailures`: Alert if `personalized_memory_compressions_total{status="error"}` > 5 in 5min.
3. Update documentation:
   - `docs/challenge_days.md` Day 25 section: Add implementation details and examples.
   - `docs/specs/epic_25/architecture.md`: Create architecture diagram and component descriptions.
   - `README.md`: Add "Personalised Butler" section linking to EP25 docs.
4. Create user guide (`docs/user_guides/personalized_butler.md`):
   - How personalisation works (persona, memory).
   - Clarify that personalisation is automatic (no public profile commands).
   - Privacy note (memory stored locally in Mongo).
5. Update metrics documentation (`docs/operational/metrics.md`):
   - Add personalisation metrics descriptions.

**Evidence**:
- CI log with integration tests passing.
- Metrics screenshots (Grafana dashboard).
- Doc diffs committed.

### TL-08 · Background Memory Compression Worker
**Purpose:** offload heavy summarisation/compression from online path and keep memory size healthy even when users exceed inline limits.

**Tasks**:
1. Implement worker script (`scripts/workers/personalization_memory_worker.py`):
   - Reads batch of user_ids with event counts > threshold (reuse `UserMemoryRepository.count_events`).
   - For each user:
     1. Fetch events older than last `keep_last_n`.
     2. Build text blob and call `MemorySummarizerService`.
     3. Invoke `UserMemoryRepository.compress(user_id, summary, keep_last_n)` and update profile summary.
   - Logs metrics per user.
2. Add scheduler:
   - Local cron entry (`cronjobs/personalization_memory_worker`) or systemd timer.
   - Document `make run-memory-worker` for manual execution.
3. Metrics & alerts:
   - `personalized_memory_worker_runs_total`, `personalized_memory_worker_errors_total`.
   - Alert if worker fails N times in a row.
4. Deployment:
   - Update README/dev handoff with instructions for enabling worker in production (e.g. `./scripts/workers/personalization_memory_worker.py --once`).

**Evidence**:
- Worker dry-run log attached to worklog.
- Metrics exposed via `/metrics` (counters increment).
- Scheduler configuration committed (or documented if ops-managed).

## 5. Testing Strategy
| Level | Suites / Files | Notes |
| --- | --- | --- |
| Unit | `tests/unit/domain/personalization/test_*.py`, `tests/unit/application/personalization/test_*.py` | Value objects, prompt assembly, use cases (mocked repos). |
| Integration | `tests/integration/infrastructure/personalization/test_repositories.py`, `tests/integration/presentation/bot/test_personalized_handlers.py` | Mongo repos (fakemongo), Telegram handlers (mock bot API). |
| E2E | `tests/e2e/personalization/test_personalized_flow.py` | Full flow: text/voice → personalized reply → memory stored. |
| Observability | `tests/integration/metrics/test_personalization_metrics.py` | Verify metrics registered and incremented. |

## 6. CI/CD Gates
| Gate | Command | Applies To | Threshold | Blocking |
| --- | --- | --- | --- | --- |
| Lint | `make lint` | All stages | 0 errors | Yes |
| Typecheck | `mypy src/ --strict` | TL-01–TL-06 | 100% coverage | Yes |
| Unit tests | `pytest tests/unit/personalization` | TL-01–TL-04 | Pass | Yes |
| Integration tests | `pytest tests/integration/personalization` | TL-05–TL-07 | Pass | Yes |
| Coverage | `pytest --cov=src --cov-report=xml` | TL-04–TL-07 | ≥80% overall | Yes |
| Metrics check | Manual: `curl http://localhost:8000/metrics \| grep personalized_` | TL-07 | All metrics visible | Yes |

## 7. Traceability
| Requirement | Stage | Evidence |
| --- | --- | --- |
| User profile persistence | TL-01 + TL-02 | Profile repo tests + metrics |
| User memory with compression | TL-02 + TL-04 | Memory repo tests + compression logic in use case |
| Personalised reply with Alfred persona | TL-03 + TL-04 | Prompt assembly tests + integration tests |
| Telegram integration (text + voice) | TL-05 | Handler tests + manual walkthrough |
| Profile commands | TL-06 | N/A for Day 25 (no public commands; admin CLI only) |
| Observability | TL-02 + TL-04 + TL-07 | Metrics + alerts + docs |

## 8. Risk Register
| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Memory grows unbounded | High | Medium | Enforce 50-event cap with inline compression; optional background worker for cleanup. |
| Persona prompt too long/noisy | Medium | Medium | Token estimation + truncation logic; keep persona section ≤200 tokens. |
| LLM failures break personalisation | High | Low | Graceful degradation: fallback to generic message; log error for monitoring. |
| Personalisation breaks existing flows | Medium | Low | Feature flag for quick disable; characterization tests for existing Butler flows. |
| Mongo performance issues | Medium | Low | Compound indexes on (user_id, created_at); monitor query latency via metrics. |

## 9. Handoff Checklist
- [ ] TL-00 decisions logged (persona, memory cap, prompt size, voice integration).
- [ ] Domain models merged with docstrings/tests.
- [ ] Repositories implemented with indexes and metrics.
- [ ] Personalisation service + use cases implemented with structured logging.
- [ ] Telegram handlers updated; voice path integrated.
- [ ] Profile commands + admin CLI implemented and tested.
- [ ] Metrics + alerts updated; docs & acceptance matrix signed.

---

**Plan Version**: 1.0
**Status**: Ready for TL-00 review and kickoff
