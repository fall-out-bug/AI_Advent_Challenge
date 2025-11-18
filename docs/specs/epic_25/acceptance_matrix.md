# Epic 25 · Acceptance Matrix (Day 25 Personalised Butler)

**Epic**: EP25 - Personalised Butler ("Alfred-style дворецкий")
**Owner**: Tech Lead
**Co-signer**: Analyst
**Version**: 1.0
**Date**: 2025-11-18

---

## Acceptance Criteria

| Task | Stage | Evidence | Owner | Status |
| --- | --- | --- | --- | --- |
| TL-00: Confirm persona ("Alfred-style дворецкий"), memory cap (50 events), LLM prompt size (≤2000 tokens), profile exposure (internal CLI only), voice integration (STT→personalised), personalisation mode (always-on with feature flag) | TL-00 | Decision log in `work_log.md`, backlog update, `tech_lead_plan.md` TL-00 section | Tech Lead | Pending |
| TL-01: Define `UserProfile`, `UserMemoryEvent`, `MemorySlice`, `PersonalizedPrompt` value objects | TL-01 | `src/domain/personalization/` modules, unit tests, docstrings | Dev A | Pending |
| TL-01: Define `UserProfileRepository`, `UserMemoryRepository`, `PersonalizationService` protocols | TL-01 | `src/domain/interfaces/personalization.py`, unit tests, protocol compliance | Dev A | Pending |
| TL-02: Implement `MongoUserProfileRepository` with indexes and auto-creation of default profile | TL-02 | `src/infrastructure/personalization/profile_repository.py`, integration tests with fakemongo, indexes verified | Dev B | Pending |
| TL-02: Implement `MongoUserMemoryRepository` with compound indexes and compression logic | TL-02 | `src/infrastructure/personalization/memory_repository.py`, integration tests, compression tests | Dev B | Pending |
| TL-02: Add Mongo migrations/indexes script for personalisation collections | TL-02 | `scripts/migrations/add_personalization_indexes.py`, successful migration run | Dev B | Pending |
| TL-02: Add metrics (`user_profile_reads/writes_total`, `user_memory_events_total`, `user_memory_compressions_total`) | TL-02 | `/metrics` endpoint snapshot, metrics tests | Dev B | Pending |
| TL-03: Implement `PersonalizationServiceImpl` with profile loading and prompt assembly | TL-03 | `src/application/personalization/personalization_service.py`, unit tests (mock repos), prompt validation | Dev A | Pending |
| TL-03: Implement `MemorySummarizerService` (optional) for background compression | TL-03 | Service module (if implemented), summarization tests with LLM | Dev A | Pending |
| TL-03: Implement prompt templates (persona, memory, full prompt) | TL-03 | `src/application/personalization/templates.py`, template validation, token estimation tests | Dev A | Pending |
| TL-04: Implement `PersonalizedReplyUseCase` with inline memory compression | TL-04 | `src/application/personalization/use_cases/personalized_reply.py`, unit tests, integration tests | Dev A | Pending |
| TL-04: Implement `ResetPersonalizationUseCase` | TL-04 | `src/application/personalization/use_cases/reset_personalization.py`, unit tests | Dev B | Pending |
| TL-04: Add structured logging (user_id, persona, memory_events_used, prompt_tokens, reply_length) | TL-04 | Log samples in test output, log format validation | Dev A | Pending |
| TL-04: Add metrics (`personalized_requests_total`, `personalized_prompt_tokens_total`, `personalized_memory_compressions_total`) | TL-04 | `/metrics` endpoint snapshot, metrics tests | Dev A | Pending |
| TL-05: Update text message handler to route through `PersonalizedReplyUseCase` | TL-05 | `src/presentation/bot/handlers/message_handler.py` diff, manual test (text → personalized reply) | Dev C | Pending |
| TL-05: Update voice message handler to route STT output through `PersonalizedReplyUseCase` | TL-05 | `src/presentation/bot/handlers/voice_handler.py` diff, manual test (voice → STT → personalized reply) | Dev C | Pending |
| TL-05: Add factory for personalization use case injection with DI | TL-05 | `src/infrastructure/personalization/factory.py`, factory tests, DI integration | Dev C | Pending |
| TL-05: Update bot initialization with personalization use cases | TL-05 | `src/presentation/bot/butler_bot.py` diff, bot startup logs | Dev C | Pending |
| TL-05: Add feature flag `PERSONALIZATION_ENABLED` (default True) | TL-05 | `src/infrastructure/config/settings.py` diff, feature flag test | Dev C | Pending |
| TL-06: Implement admin CLI tool (`profile_admin.py`) with list/show/reset/update commands (no public profile commands) | TL-06 | `scripts/tools/profile_admin.py`, CLI tests, manual walkthrough | Dev C | Pending |
| TL-07: Expand integration tests (E2E text → personalized reply, voice → STT → personalized reply, memory compression) | TL-07 | Test suites in `tests/integration/personalization/`, `tests/e2e/personalization/`, CI log | QA | Pending |
| TL-07: Add Prometheus alerts (`PersonalizationHighErrorRate`, `MemoryCompressionFailures`) | TL-07 | `config/prometheus/alerts/personalization.yml`, alert validation | Tech Lead | Pending |
| TL-07: Update documentation (`challenge_days.md`, `architect_plan.md`, `README.md`, `user_guides/personalized_butler.md`, `operational/metrics.md`) | TL-07 | Doc diffs, content review | Tech Lead | Pending |
| TL-08: Implement background memory compression worker + scheduler + metrics | TL-08 | `scripts/workers/personalization_memory_worker.py`, scheduler docs, `/metrics` counters | Dev B | Pending |

**Status Legend**: Pending / In Progress / Done / Blocked

---

## Production Readiness Checklist

- [ ] **Domain Layer**: All value objects and protocols defined with 100% type hints and docstrings
- [ ] **Infrastructure Layer**: Mongo repositories implemented with indexes, metrics, error handling
- [ ] **Application Layer**: Use cases implemented with structured logging, graceful degradation
- [ ] **Presentation Layer**: Telegram handlers updated, voice integration working, feature flag added
- [ ] **Commands & Tools**: Admin CLI (`profile_admin.py`) implemented and tested (no public profile commands)
- [ ] **Testing**: Unit tests (≥80% coverage), integration tests, E2E tests passing
- [ ] **Observability**: Metrics registered, alerts configured, logs structured
- [ ] **Documentation**: Architecture docs, user guide, API docs updated
- [ ] **Configuration**: All settings externalized via environment variables
- [ ] **Migration**: Mongo indexes created, deployment script updated

---

## Evidence Artifacts

### Code Deliverables
- `src/domain/personalization/` - Domain models (UserProfile, UserMemoryEvent, MemorySlice, PersonalizedPrompt)
- `src/domain/interfaces/personalization.py` - Repository and service protocols
- `src/infrastructure/personalization/` - Mongo repositories (profile, memory)
- `src/application/personalization/` - Use cases (PersonalizedReplyUseCase, ResetPersonalizationUseCase), service, templates
- `src/presentation/bot/handlers/` - Updated handlers (message_handler.py, voice_handler.py, profile_handler.py)
- `scripts/tools/profile_admin.py` - Admin CLI tool
- `scripts/migrations/add_personalization_indexes.py` - Mongo migrations
- `scripts/workers/personalization_memory_worker.py` - Background memory compression worker

### Test Deliverables
- `tests/unit/domain/personalization/` - Value object tests
- `tests/unit/application/personalization/` - Use case and service tests
- `tests/integration/infrastructure/personalization/` - Repository integration tests
- `tests/integration/presentation/bot/` - Handler integration tests
- `tests/e2e/personalization/` - End-to-end flow tests
- `tests/integration/metrics/test_personalization_metrics.py` - Metrics tests

### Documentation Deliverables
- `docs/specs/epic_25/tech_lead_plan.md` - Tech Lead implementation plan
- `docs/specs/epic_25/acceptance_matrix.md` - This acceptance matrix
- `docs/specs/epic_25/architect_plan.md` - Architecture diagram and component descriptions
- `docs/challenge_days.md` - Day 25 section updated
- `docs/user_guides/personalized_butler.md` - User guide for personalisation
- `docs/operational/metrics.md` - Personalisation metrics documentation
- `README.md` - Updated with personalisation section

### Observability Deliverables
- Metrics: `user_profile_reads_total`, `user_profile_writes_total`, `user_memory_events_total`, `user_memory_compressions_total`, `personalized_requests_total`, `personalized_prompt_tokens_total`
- Alerts: `PersonalizationHighErrorRate`, `MemoryCompressionFailures`
- Logs: Structured logs with `user_id`, `persona`, `memory_events_used`, `prompt_tokens`, `reply_length`
- Worker Metrics: `personalized_memory_worker_runs_total`, `personalized_memory_worker_errors_total`

---

## Review Sign-Off

**Tech Lead**: ________________ (Date: ________)
**Analyst**: ________________ (Date: ________)

---

**Matrix Version**: 1.0
**Status**: Ready for TL-00 kickoff
