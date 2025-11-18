# Stage TL-00: Scope Confirmation & Decisions

**Epic**: EP25 - Personalised Butler
**Stage**: TL-00
**Duration**: 1 day
**Owner**: Tech Lead
**Status**: Ready

---

## Goal

Finalize all architectural decisions and prepare detailed backlog for implementation.

---

## Objectives

1. Confirm persona template and tone
2. Confirm memory management strategy
3. Confirm LLM prompt constraints
4. Confirm feature flag approach
5. Document all decisions for team alignment

---

## Key Decisions

### Decision 1: Persona Template

**Question**: What persona should Butler use?

**Decision**: "Alfred-style дворецкий" (Alfred Pennyworth from Batman)

**Details**:
- **Character**: Alfred Pennyworth (Batman's butler)
- **Traits**: Polite, ironic, caring, witty, respectful
- **Style**: English humour, Russian language
- **Tone**: Helpful and informative with light sarcasm

**Example Interactions**:
```
User: "Привет!"
Butler: "Добрый день, сэр. Надеюсь, день проходит без излишней драмы? Чем могу быть полезен?"

User: "Что нового?"
Butler: "Ах, вечный вопрос. Позвольте проверить свои архивы..."
```

**Rationale**: Alfred persona provides perfect balance between professionalism and personality, making interactions engaging while maintaining respect.

---

### Decision 2: Memory Management Strategy

**Question**: How should we manage growing user memory?

**Decision**: Cap at 50 events per user with inline compression

**Details**:
- **Memory Cap**: 50 events (user + assistant messages)
- **Compression Trigger**: Automatically when count >50
- **Compression Process**:
  1. Load all events for user
  2. Summarize via local LLM (max 300 tokens)
  3. Delete old events, keep last 20
  4. Update profile with summary
- **Auto-Cleanup**: TTL index (90 days) for archived events

**Rationale**:
- 50 events = ~25 conversation turns, sufficient for context
- Inline compression keeps system simple (no background worker needed initially)
- 20 retained events maintain recent context
- LLM summarization preserves important historical context

---

### Decision 3: LLM Prompt Constraints

**Question**: What are the prompt size limits for local LLM?

**Decision**: Target ≤2000 tokens per personalized prompt

**Details**:
- **LLM Context Window**: Qwen-7B = 4096 tokens
- **Personalized Prompt Budget**: ≤2000 tokens
  - Persona section: ≤200 tokens
  - Memory context: ≤800 tokens
  - Memory summary: ≤300 tokens
  - New message: ≤200 tokens
  - Buffer for LLM response: ≤500 tokens
- **Truncation Strategy**: If prompt >2000 tokens → keep summary + last 5 events

**Token Estimation**: Simple heuristic (4 chars ≈ 1 token)

**Rationale**: Conservative limit ensures reliable generation with room for response, prevents context overflow.

---

### Decision 4: Feature Flag Approach

**Question**: Should personalization be always-on or opt-in?

**Decision**: Opt-in with feature flag (PERSONALIZATION_ENABLED=false by default)

**Details**:
- **Feature Flag**: `PERSONALIZATION_ENABLED` environment variable
- **Default**: `false` (disabled)
- **Rollout Strategy**:
  1. Deploy with flag disabled
  2. Enable for internal testing
  3. Enable for beta users (via admin tool)
  4. Gradual rollout to all users
  5. Default to `true` after stabilization
- **Fallback**: If disabled, route through existing ButlerOrchestrator

**Rationale**: Gradual rollout reduces risk, allows monitoring before full deployment, enables quick rollback if issues arise.

---

### Decision 5: Profile Management

**Question**: Should users configure profiles via Telegram commands?

**Decision**: Internal admin tool only (no public profile commands in MVP)

**Details**:
- **MVP Scope**: All users get default "Alfred-style дворецкий" persona automatically
- **Admin Tool**: CLI tool (`profile_admin.py`) for internal management
  - `list` - show all profiles
  - `show <user_id>` - show profile + memory stats
  - `reset <user_id>` - reset profile and memory
  - `update <user_id>` - update persona/tone/language
- **Future**: Public profile commands in later iteration

**Rationale**: Simpler MVP, focuses on core functionality, reduces scope creep.

---

### Decision 6: Voice Integration

**Question**: How should voice messages integrate with personalization?

**Decision**: Route all voice messages through PersonalizedReplyUseCase (text replies only)

**Details**:
- **Flow**: Voice → STT (Whisper) → Text → PersonalizedReplyUseCase → Text reply
- **No Voice Replies**: Butler responds with text (not voice synthesis)
- **Memory**: Voice interactions stored same as text (role="user", role="assistant")
- **Source Tracking**: Tag events with source="voice" for analytics

**Rationale**: Reuses existing EP24 STT infrastructure, keeps complexity low, voice synthesis out of scope for MVP.

---

### Decision 7: Testing Strategy

**Question**: What testing coverage is needed?

**Decision**: Unit + Integration tests (~80% coverage)

**Details**:
- **Unit Tests**:
  - All domain value objects
  - All use cases (with mocked repos)
  - Prompt assembly logic
  - Token estimation
- **Integration Tests**:
  - Mongo repositories (with testcontainers or fakemongo)
  - Telegram handlers (mock bot API)
  - E2E: Text → personalized reply → memory stored
  - E2E: Voice → STT → personalized reply → memory stored
  - Memory compression (>50 events)
- **Manual Tests**:
  - Send text message → verify Alfred-style reply
  - Send voice message → verify personalized reply
  - CLI tools → verify CRUD operations

**Coverage Target**: ≥80% overall, 100% for domain layer

**Rationale**: Balances quality with velocity, focuses on critical paths, ensures reliable production deployment.

---

## Architecture Principles

### Clean Architecture Compliance

**Layer Separation**:
1. **Domain Layer**: Pure business logic, no external dependencies
   - Value objects: UserProfile, UserMemoryEvent, MemorySlice, PersonalizedPrompt
   - Protocols: Repository and service interfaces

2. **Application Layer**: Use cases and orchestration
   - Use cases: PersonalizedReplyUseCase, ResetPersonalizationUseCase
   - Services: PersonalizationServiceImpl
   - Templates: Prompt templates

3. **Infrastructure Layer**: External integrations
   - Repositories: MongoUserProfileRepository, MongoUserMemoryRepository
   - Metrics: Prometheus counters and histograms

4. **Presentation Layer**: API and bot handlers
   - Handlers: Updated message_handler, voice_handler
   - CLI: profile_admin.py

**Dependency Rule**: Inner layers never depend on outer layers

---

### Clean Code Principles

**Code Quality Standards**:
- **PEP 8** compliance (88 char line length)
- **Type hints** required (100% coverage, mypy strict mode)
- **Docstrings** required (Google style, English)
- **Functions** ≤15 lines where possible
- **Single Responsibility** per function/class
- **No magic numbers** (use named constants)
- **Error handling** with specific exceptions
- **Structured logging** with context

---

## Backlog Updates

### Tasks to Document

1. **TL-01**: Domain models & interfaces (1.5 days)
2. **TL-02**: Infrastructure repositories (2 days)
3. **TL-03**: Personalization service & prompt assembly (1.5 days)
4. **TL-04**: Personalized reply use case (2 days)
5. **TL-05**: Telegram bot integration (2 days)
6. **TL-06**: Admin tools (1 day)
7. **TL-07**: Testing, observability, docs (1.5 days)
8. **TL-08**: Background memory compression worker (2 days)

**Total Estimated Duration**: ~11.5 days

---

## Deliverables

### Documentation

- [x] Decision log (this document)
- [ ] Updated `backlog.md` with confirmed tasks
- [ ] Updated `tech_lead_plan.md` with decisions
- [ ] Stage specifications (TL-01 to TL-08)

### Communication

- [ ] Team alignment meeting (decisions review)
- [ ] Stakeholder briefing (scope confirmation)
- [ ] Developer kickoff (architecture overview)

---

## Acceptance Criteria

- [x] All architectural decisions documented
- [x] Feature flag approach confirmed (opt-in)
- [x] Voice integration strategy confirmed (text replies)
- [x] Testing strategy confirmed (80% coverage)
- [x] Clean Architecture principles documented
- [ ] Team alignment completed
- [ ] Stage specifications created (TL-01 to TL-08)

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Persona not engaging | Medium | Low | A/B test with users, iterate based on feedback |
| Memory grows too fast | Medium | Medium | Monitor event counts, tune compression threshold |
| Prompt too long | High | Medium | Aggressive truncation, token monitoring |
| Feature flag bugs | High | Low | Thorough testing, gradual rollout |
| LLM summarization poor | Medium | Medium | Test summarization quality, tune prompts |

---

## Next Steps

1. Create stage specifications (TL-01 to TL-08)
2. Schedule team alignment meeting
3. Begin TL-01 implementation (domain models)

---

**Status**: ✅ Complete
**Sign-off**: Tech Lead
**Date**: 2025-11-18
