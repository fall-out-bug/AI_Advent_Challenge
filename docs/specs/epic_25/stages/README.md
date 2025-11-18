# Epic 25 Stage Specifications

**Epic**: EP25 - Personalised Butler  
**Status**: Ready for Implementation  
**Created**: 2025-11-18

---

## Overview

This directory contains detailed implementation specifications for each stage of Epic 25. Each specification provides:
- Goals and objectives
- Detailed implementation guidance
- Code examples and templates
- Testing requirements
- Acceptance criteria
- Dependencies and deliverables

---

## Stage Index

### Core Implementation (MVP)

| Stage | Title | Duration | Priority | Status |
|-------|-------|----------|----------|--------|
| [TL-00](./TL-00_scope_confirmation.md) | Scope Confirmation & Decisions | 1 day | High | Ready |
| [TL-01](./TL-01_domain_models.md) | Domain Models & Interfaces | 1.5 days | High | Pending |
| [TL-02](./TL-02_infrastructure_repositories.md) | Infrastructure Repositories | 2 days | High | Pending |
| [TL-03](./TL-03_personalization_service.md) | Personalization Service & Prompt Assembly | 1.5 days | High | Pending |
| [TL-04](./TL-04_personalized_reply_use_case.md) | Personalized Reply Use Case | 2 days | High | Pending |
| [TL-05](./TL-05_telegram_bot_integration.md) | Telegram Bot Integration | 2 days | High | Pending |
| [TL-06](./TL-06_admin_tools.md) | Admin Tools Only | 1 day | Medium | Pending |
| [TL-07](./TL-07_testing_observability_docs.md) | Testing, Observability & Documentation | 1.5 days | High | Pending |

**Total MVP Duration**: ~11.5 days

### Optional Enhancement

| Stage | Title | Duration | Priority | Status |
|-------|-------|----------|----------|--------|
| [TL-08](./TL-08_background_memory_worker.md) | Background Memory Compression Worker | 2 days | Low | Optional |

---

## Stage Descriptions

### TL-00: Scope Confirmation & Decisions

**Purpose**: Finalize all architectural decisions and document scope.

**Key Decisions**:
- Persona: "Alfred-style дворецкий"
- Memory cap: 50 events per user
- Feature flag: PERSONALIZATION_ENABLED=false (opt-in)
- Voice integration: STT → personalized reply (text only)
- Testing: Unit + Integration (~80% coverage)

**Deliverables**: Decision log, updated backlog, stage specifications

---

### TL-01: Domain Models & Interfaces

**Purpose**: Define domain layer foundation with value objects and protocols.

**Key Components**:
- Value objects: `UserProfile`, `UserMemoryEvent`, `MemorySlice`, `PersonalizedPrompt`
- Protocols: `UserProfileRepository`, `UserMemoryRepository`, `PersonalizationService`

**Deliverables**: Domain models, protocols, unit tests (100% coverage)

---

### TL-02: Infrastructure Repositories

**Purpose**: Implement Mongo-backed repositories with indexes and metrics.

**Key Components**:
- `MongoUserProfileRepository`: Profile storage with auto-creation
- `MongoUserMemoryRepository`: Event storage with compression support
- Mongo indexes: user_id unique, (user_id, created_at) compound, TTL (90 days)
- Prometheus metrics: profile reads/writes, memory events, compressions

**Deliverables**: Repositories, metrics, migration script, integration tests

---

### TL-03: Personalization Service & Prompt Assembly

**Purpose**: Build personalized prompts from profile + memory context.

**Key Components**:
- Prompt templates: persona, memory context, full prompt
- `PersonalizationServiceImpl`: Profile loading, prompt assembly
- Token estimation and truncation logic

**Deliverables**: Service, templates, unit tests

---

### TL-04: Personalized Reply Use Case

**Purpose**: Orchestrate profile loading, memory management, LLM generation.

**Key Components**:
- `PersonalizedReplyUseCase`: Main orchestration
- `ResetPersonalizationUseCase`: Profile/memory reset
- Inline memory compression (>50 events → compress)
- DTOs: Input/Output data transfer objects

**Deliverables**: Use cases, DTOs, unit + integration tests

---

### TL-05: Telegram Bot Integration

**Purpose**: Integrate personalization into bot handlers with feature flag.

**Key Components**:
- Feature flag: `PERSONALIZATION_ENABLED` (default: false)
- Updated `butler_handler.py`: Route through personalization if enabled
- Updated `voice_handler.py`: STT → personalization
- Factory: DI for use cases
- Bot initialization: Create use cases if enabled

**Deliverables**: Updated handlers, factory, integration tests

---

### TL-06: Admin Tools Only

**Purpose**: Create internal CLI for profile/memory management.

**Key Components**:
- CLI tool: `profile_admin.py`
- Commands: list, show, reset, update
- Rich terminal output (tables, colors)
- Confirmation prompts for destructive operations

**Deliverables**: CLI tool, usage documentation, tests

---

### TL-07: Testing, Observability & Documentation

**Purpose**: Expand test coverage, add alerts, complete documentation.

**Key Components**:
- E2E tests: Text flow, voice flow, compression flow
- Prometheus alerts: High error rate, compression failures, latency
- User guide: Personalized Butler usage
- Project docs: Updated README, challenge_days.md
- Metrics docs: Operational metrics guide

**Deliverables**: E2E tests, alerts, documentation, final report

---

### TL-08: Background Memory Compression Worker (Optional)

**Purpose**: Offload memory compression from request handlers to background worker.

**Key Components**:
- Background worker script: `personalization_memory_worker.py`
- Distributed locking: Redis-based lock to prevent overlaps
- Scheduler: Cron or systemd timer (daily at 2 AM)
- Worker metrics: Runs, errors, users processed, duration

**Deliverables**: Worker script, scheduler config, runbook, tests

**When to Skip**: Low user count (<100), inline compression fast enough, limited team bandwidth

---

## Implementation Order

### Recommended Sequence

1. **TL-00**: Decision confirmation (prerequisite for all)
2. **TL-01**: Domain models (foundation)
3. **TL-02**: Repositories (data layer)
4. **TL-03**: Personalization service (business logic)
5. **TL-04**: Use cases (orchestration)
6. **TL-05**: Bot integration (presentation layer)
7. **TL-06**: Admin tools (operations support)
8. **TL-07**: Testing & docs (quality assurance)
9. **TL-08**: Background worker (optional enhancement)

### Parallelization Opportunities

- **TL-01 + TL-02**: Can be developed in parallel by different devs
- **TL-06**: Can start after TL-04 (independent of TL-05)
- **TL-07**: E2E tests can be written during TL-05/TL-06

---

## Dependencies

```
TL-00 (Decisions)
  ├── TL-01 (Domain)
  │     ├── TL-02 (Infrastructure)
  │     │     ├── TL-03 (Service)
  │     │     │     └── TL-04 (Use Cases)
  │     │     │           ├── TL-05 (Bot Integration)
  │     │     │           │     ├── TL-06 (Admin Tools)
  │     │     │           │     │     └── TL-07 (Testing & Docs)
  │     │     │           │     │           └── TL-08 (Worker, Optional)
```

---

## Testing Strategy

### Unit Tests (TL-01, TL-03, TL-04)
- Domain value objects: 100% coverage
- Service logic: ≥80% coverage
- Use cases: ≥80% coverage
- Mock all external dependencies

### Integration Tests (TL-02, TL-04, TL-05, TL-06)
- Repositories with testcontainers or fakemongo
- Bot handlers with mocked bot API
- CLI tools with test database
- ≥80% coverage for integration paths

### E2E Tests (TL-07)
- Full flow with real services
- Text → personalized reply → memory stored
- Voice → STT → personalized reply
- >50 messages → compression triggered

---

## Acceptance Checklist

### Code Quality
- [ ] 100% type hints (mypy strict mode)
- [ ] All docstrings complete (Google style)
- [ ] PEP 8 compliance (Black formatter)
- [ ] Functions ≤15 lines where possible
- [ ] No magic numbers (named constants)

### Testing
- [ ] Unit tests: ≥80% coverage
- [ ] Integration tests: ≥80% coverage
- [ ] E2E tests: Critical flows covered
- [ ] All tests passing in CI

### Architecture
- [ ] Clean Architecture principles followed
- [ ] Layer boundaries respected
- [ ] Protocols used for interfaces
- [ ] Dependency injection via factories

### Documentation
- [ ] Code documented (docstrings)
- [ ] User guide complete
- [ ] Operational runbooks complete
- [ ] README updated
- [ ] Metrics documented

### Observability
- [ ] Metrics registered and tested
- [ ] Prometheus alerts configured
- [ ] Structured logging implemented
- [ ] Runbooks for common issues

---

## Review Process

### Stage Sign-Off

Each stage requires sign-off before proceeding:
1. **Code Review**: Tech Lead approval
2. **Testing**: QA verification (unit + integration passing)
3. **Documentation**: Docs review complete
4. **Demo**: Stage demo to stakeholders (if applicable)

### Epic Sign-Off

After TL-07 completion:
1. **Full Test Suite**: All tests passing (unit + integration + E2E)
2. **Documentation Review**: All docs complete and accurate
3. **Metrics Validation**: Metrics visible in Prometheus
4. **Acceptance Matrix**: All criteria met
5. **Final Report**: Epic completion report approved

---

## Rollout Plan

### Phase 1: Internal Testing (TL-05)
- Deploy with PERSONALIZATION_ENABLED=false
- Enable for specific test users (manual config)
- Collect feedback and iterate

### Phase 2: Beta Testing (TL-07)
- Enable for beta user group (10-20 users)
- Monitor metrics and logs
- Fix issues and refine persona

### Phase 3: Full Rollout (Post TL-07)
- Enable PERSONALIZATION_ENABLED=true by default
- Monitor error rates and performance
- Quick rollback plan if needed

---

## Resources

### Documentation
- Epic Overview: `../epic_25.md`
- Tech Lead Plan: `../tech_lead_plan.md`
- Acceptance Matrix: `../acceptance_matrix.md`
- Developer Handoff: `../dev_handoff.md`

### References
- Clean Architecture: `docs/architecture.md`
- Cursor Rules: `.cursor/rules/cursorrules-unified.md`
- Coding Standards: `docs/guides/coding_standards.md`

---

## Contact

**Tech Lead**: cursor_tech_lead_v1  
**Epic Owner**: Tech Lead  
**Questions**: See `../README.md` for contact information

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-18  
**Status**: Ready for Implementation

