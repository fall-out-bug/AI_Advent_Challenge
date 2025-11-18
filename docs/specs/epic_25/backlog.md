# Epic 25 Backlog · Personalised Butler (“Alfred-style дворецкий”)

## Context
Day 25 introduces personalisation for the Butler Telegram bot. The focus is on:
- Persona (“Alfred-style дворецкий”: snarky but caring, English humour, speaks Russian),
- Per-user profile (language, tone, focus),
- Per-user memory of previous interactions with periodic compression,
while staying on existing local/shared infrastructure.

## Tasks

### 1. Domain Models & Interfaces
1. **Define `UserProfile` value object**
   - Fields: `user_id`, `language`, `persona`, `tone`, `preferred_topics` (optional).
   - Validation and sensible defaults (RU, “Alfred-style дворецкий” persona).
2. **Define `UserMemoryEvent`**
   - Fields: `user_id`, `timestamp`, `role` (`user` / `assistant`), `content`, optional `tags`.
3. **Define repositories & service interfaces**
   - `UserProfileRepository` with `get`, `save`, `reset`.
   - `UserMemoryRepository` with `append_event`, `get_recent_events(user_id, limit)`.
   - `PersonalizationService` with:
     - `load_profile(user_id) -> UserProfile`
     - `build_persona_prompt(user_id) -> str`
     - `load_recent_memory(user_id, limit) -> list[UserMemoryEvent]`.

### 2. Infrastructure Repositories (Mongo)
4. **MongoUserProfileRepository**
   - Collection: `user_profiles`.
   - Methods: `get` (create default if not exists), `save`, `reset`.
   - Index on `user_id`.
5. **MongoUserMemoryRepository**
   - Collection: `user_memory`.
   - Methods: `append_event`, `get_recent_events` with sort by `timestamp`.
   - Index on `(user_id, timestamp)`.

### 3. Personalised Reply Use Case
6. **Implement `GetPersonalizedReplyUseCase`**
   - Input: `user_id`, `text` (string), optional `source` (`text` / `voice`).
   - Steps:
     1. Load profile via `PersonalizationService`.
     2. Load recent memory events.
     3. Build persona+memory+message prompt.
     4. Call local LLM client (existing infra).
     5. Append new `user` and `assistant` events to memory.
   - Output: reply text and metadata (e.g. `used_persona=True`).

### 4. Telegram Bot Integration
7. **Route text messages through personalised use case**
   - For standard text updates: resolve `user_id`, call `GetPersonalizedReplyUseCase`, send reply.
8. **Reuse Day 24 voice path**
   - After STT transcription: instead of direct Butler call, pass transcription to the personalised use case.

### 5. Admin Tooling (CLI only)
9. **Implement `profile_admin.py` CLI tool**
   - Internal admin tool to list/show/reset/update profiles and inspect memory stats.
10. **Document CLI usage**
    - Short developer doc snippet describing how to run the CLI; no public Telegram commands in Day 25.

### 6. Observability & Docs
11. **Add metrics**
    - `user_profile_reads_total`, `user_profile_writes_total`.
    - `user_memory_events_total`, `personalized_requests_total`.
12. **Update docs**
    - Add Day 25 details to `docs/challenge_days.md` (done at high level; update with implementation specifics when ready).
    - Add a short “Personalised Butler” section in `README*` or link to Epic 25 summary.

### 7. Background Memory Compression Worker
13. **Implement `personalization_memory_worker.py`**
    - Scan Mongo for users with >50 events.
    - Summarize old events via LLM and replace them with compressed summary in profile + last N events.
    - Emit metrics/alerts per run.
14. **Add scheduler for worker**
    - Cron/systemd entry or documented manual run (`make run-memory-worker`).
    - Ensure worker run is idempotent and has locking to avoid overlap.
15. **Document worker operation**
    - Developer note on enabling worker and feature flag (if any).
    - Add metrics/alert references to `docs/operational/metrics.md`.

### 8. Interest Extraction & Profile Enrichment
16. **Extract user interests from conversation during summarisation**
    - Extend memory summarisation prompts to detect recurring topics, technologies and domains the user cares about.
    - Parse summarisation output and update `UserProfile.preferred_topics` with a small, stable list of interests (e.g. 3–7 items).
    - Ensure `PersonalizationService` passes `preferred_topics` into the persona prompt so Butler can adapt examples, suggestions and wording to these interests.
    - Avoid storing sensitive data as interests (no raw secrets, tokens, IDs); focus on thematic topics (e.g. "Python", "LLM orchestration", "Telegram bots").
    - Add lightweight tests to verify that after several themed conversations `preferred_topics` contains relevant topics and they are reflected in replies (e.g. examples or suggestions in user’s domains).

## Done When
- All tasks 1–12 implemented.
- Personalised replies work for text and voice messages in Telegram.
- Metrics and docs reflect personalisation behaviour.
