# Epic 21 · Risk Register

| Risk ID | Category | Description | Probability | Impact | Mitigation | Contingency |
|---------|----------|-------------|-------------|--------|------------|-------------|
| R-21-01 | Data Integrity | Dialog context migration corrupts Mongo documents | Medium | High | Characterization tests + backup snapshots before rollout | Roll back to previous repository implementation using feature flag |
| R-21-02 | Performance | DI indirection increases dialog latency beyond 100 ms p95 | Medium | High | Benchmark before/after each sub-stage, optimize hot paths | Disable new DI layer via feature flag, profile with sampling |
| R-21-03 | Storage Reliability | New storage adapter fails (checksum, disk full) | High | Critical | Dual-write during cutover, checksum validation, alerting on failures | Purge corrupted artifacts, fall back to legacy path |
| R-21-04 | External Dependency | HW checker downtime impacts Homework service abstraction | Medium | Medium | Implement retries + circuit breaker, cache latest status | Graceful degradation message, manual retry tool |
| R-21-05 | Concurrency | Race conditions in new repositories/adapters | Low | High | Add async stress tests, use optimistic locking where applicable | Revert to legacy implementations, patch concurrency guard |
| R-21-06 | Scope Creep | Parallel refactors exceed capacity | High | Medium | Follow roadmap (one component at a time), weekly scope review | Defer lower-priority tasks to follow-up epic |
| R-21-07 | Security | Missing AV hook or env misconfig exposes storage | Low | High | Optional AV integration, config validation in CI | Disable storage feature flag, rotate credentials |
| R-21-08 | Observability | Metrics/alerts misconfigured leading to blind spots | Medium | Medium | Validate metrics via promtool, run alert simulations | Re-run previous dashboards, raise manual smoke alerts |

*Last updated: 2025-11-11*

