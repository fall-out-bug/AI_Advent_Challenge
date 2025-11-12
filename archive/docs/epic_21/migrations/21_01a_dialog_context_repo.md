# Migration Notes · 21_01a Dialog Context Repository

> Template based on `docs/specs/epic_21/architect/migration_notes_template.md`.  
> To be completed during Stage 21_01a implementation.

## Summary
- Introduce `DialogContextRepository` protocol and wire Mongo adapter via DI.
- Replace direct `AsyncIOMotorDatabase` access in `ButlerOrchestrator`.
- Ensure existing dialog context documents remain compatible.

## Motivation
- Restore Clean Architecture boundaries between domain and infrastructure.
- Improve testability by enabling in-memory repository doubles.
- Provide feature-flagged rollout path with rollback support.

## Current Behaviour (Baseline)
- `ButlerOrchestrator` depends on `mongodb.dialog_contexts` collection directly.
- Context CRUD operations performed inline without abstraction.
- Characterization tests (PREP-21-02) will capture read/write behaviour prior to refactor.

## Proposed Changes
- Define `DialogContextRepository` interface in `src/domain/interfaces/`.
- Implement `MongoDialogContextRepository` in infrastructure layer.
- Update orchestrator/service constructors to accept repository dependency.
- Introduce feature flag `USE_DIALOG_CONTEXT_REPO` controlling new path.

## Data Migration Plan
- No schema changes expected.
- Validate existing documents load through repository adapter.
- Optional: backfill indexes if repository introduces new query patterns.

## Rollout Steps
1. Ship repository code behind disabled feature flag.
2. Run characterization tests + new unit/integration suites.
3. Enable flag in staging; monitor dialog latency & error rates.
4. Gradually enable in production (percentage-based or per environment).

## Rollback Plan
- Disable feature flag to revert to legacy inline Mongo access.
- Retain legacy code path until Stage 21_01a signed off.
- If data anomalies detected, restore from pre-change backups.

## Monitoring & Alerts
- Metrics: `dialog_context_repository_operations_total`, `dialog_context_repository_latency_seconds`.
- Alerts: high error rate (>5% over 5m), latency p95 > 150 ms.
- Logs: include `trace_id`, `operation`, `status`.

## Open Questions
- Confirm whether additional indexes required for repository queries.
- Decide on caching strategy (if any) post-refactor.

## Checklist
- [ ] Characterization tests created and passing.
- [ ] Repository interface + adapter implemented.
- [ ] Feature flag added to config.
- [ ] Migration validated in staging.
- [ ] Runbook updated with new operational steps.


