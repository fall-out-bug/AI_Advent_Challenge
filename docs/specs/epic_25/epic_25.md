# Epic 25 · Personalised Butler · “Alfred-style дворецкий” (Day 25)

## Context
- Day 25 builds on the existing Butler Telegram bot, observability stack (EP23), repository refactor & RAG++ (EP21), and voice support (EP24).
- The goal is to turn Butler into a **personalised assistant** that:
  - knows the user’s preferences (persona, language, tone, focus),
  - remembers past interactions,
  - and uses this information when generating replies,
  - while running entirely on local/shared infra (no external SaaS).

## Goals
1. Introduce a **User Profile & Memory** model so the bot can remember who the user is, how to talk, and what they asked before.
2. Implement a **personalised reply pipeline** that enriches prompts for the local LLM with persona (“Alfred-style дворецкий”) and recent user-specific context.
3. Integrate personalisation into the existing Telegram bot (text + voice from Day 24), with minimal changes to the Butler core.

## Success Metrics
- ✅ User profile is persisted (Mongo) and transparently used by the bot (no public configuration commands).
- ✅ For a given `user_id`, the system stores and retrieves recent dialogue history (with periodic compression) and uses it in personalised replies.
- ✅ LLM replies reflect the persona “Alfred-style дворецкий” (snarky but caring) and Russian language, without external network calls.
- ✅ Existing Butler functionality (digest, general Q&A) continues to work; personalisation is a layer on top, not a breaking change.

## Scope

### Must Have
- **User Profile**:
  - Define `UserProfile` (language, persona, tone, preferred topics).
  - CRUD operations for a single profile per `user_id`.
  - Profile is used internally only (MVP: preconfigured persona, no public Telegram commands).
- **User Memory**:
  - Store per-user interaction events (user messages + bot replies) in Mongo.
  - Load N most recent events to build context for replies and periodically compress older history (summary + last messages).
- **Personalised Reply Use Case**:
  - New application use case that:
    1. loads `UserProfile`,
    2. loads recent `UserMemory` events,
    3. builds a personalised prompt (persona + memory + new message),
    4. calls local LLM client,
    5. logs/saves interaction as new memory events.
- **Telegram Integration**:
  - Always route standard text messages through the personalised reply use case (personalisation is always on).
  - For Day 24 voice messages: reuse transcription output as text input to the personalised path; responses remain text-only.

### Should Have
- Simple developer utility (script/CLI) to reset profile/memory for a user (no public Telegram commands).
- Metrics for profile/memory usage (reads/writes, personalised requests).

### Out of Scope
- Deep homework/MCP integration (automatic use of `student_id` / progress).
- Cross-device identity management beyond Telegram `user_id`.

## Workstreams & Requirements

See `docs/specs/epic_25/backlog.md` for detailed tasks. High-level workstreams:

1. **Domain Models & Interfaces**
   - Add `UserProfile`, `UserMemoryEvent` value objects.
   - Define `UserProfileRepository` and `UserMemoryRepository` interfaces.
   - Define `PersonalizationService` interface to build persona prompts.

2. **Infrastructure Repositories**
   - Implement Mongo-backed repositories for profiles and memory events.
   - Ensure indexes on `user_id` and timestamp for efficient retrieval.

3. **Personalised Reply Use Case**
   - Implement application-layer use case taking `user_id` + text (or transcription).
   - Compose persona + recent memory + new message into a prompt.
   - Use existing local LLM client; handle errors gracefully.

4. **Telegram Bot Integration**
   - Extend existing handlers to:
     - call personalised use case for text messages,
     - reuse Day 24 path for voice messages → text → personalised reply.
   - No additional public profile commands in Day 25; personalisation is automatic for all users.

5. **Observability & Docs**
   - Metrics: `user_profile_reads_total`, `user_profile_writes_total`, `user_memory_events_total`, `personalized_requests_total`.
   - Docs: update `README*`, `docs/challenge_days.md` (Day 25), and add short user guide for personalisation.

## Acceptance Checklist
- [ ] User profile model and repository implemented; profile is automatically used in bot replies.
- [ ] User memory repository implemented; recent and summarised interactions can be listed/debugged per user.
- [ ] Personalised reply use case composes persona+memory into prompts and uses local LLM only.
- [ ] Telegram bot sends replies in the “Alfred-style дворецкий” persona for the user.
- [ ] Voice messages (from Day 24) also go through personalised reply flow after transcription (text replies).
- [ ] Metrics and basic docs updated to reflect personalisation features.

## Dependencies
- Local/shared infra: MongoDB, local LLM API (Qwen/compatible), existing Butler bot and orchestrator.
- Day 23 observability and Day 24 voice integration.

## Risks & Mitigations
- **Risk:** Memory grows unbounded.  
  **Mitigation:** Limit stored events per user (e.g. last N events or time-based TTL).

- **Risk:** Persona prompt too long / noisy.  
  **Mitigation:** Compress/summarise older memory; keep persona section short and focused.

- **Risk:** Personalisation breaks existing flows.  
  **Mitigation:** Start with a dedicated `/personal` mode or feature flag; roll out gradually.


