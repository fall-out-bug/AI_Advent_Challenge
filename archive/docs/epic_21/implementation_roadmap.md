# Epic 21 · Implementation Roadmap

## Purpose
Translate Stage 21 specifications into executable work with concrete sequencing,
test-first guidance, and migration checkpoints. This roadmap responds to developer
feedback (2025-11-11) and aligns with architect proposals.

## Guiding Principles
- **TDD first**: Every refactor starts with characterization tests capturing current behaviour.
- **Incremental delivery**: Complete one sub-component end-to-end before moving to the next.
- **Feature-flagged rollout**: Enable new implementations behind toggles with rollback paths.
- **Performance guardrails**: Measure latency/throughput/memory before and after each sub-stage.

## Phase 0 · Preparation (Stage 21_00)
| Step | Description | Deliverables | Owners |
|------|-------------|--------------|--------|
| P0.1 | Capture baseline metrics | Dialog latency (<100 ms p95), review submission (<30 s p95), worker memory (<500 MB) | DevOps |
| P0.2 | Author characterization suites | `tests/epic21/` with markers (`epic21`, `stage_21_01`, etc.) covering current flows | QA / Tech Lead |
| P0.3 | Create DI scaffolding | Manual DI factories + wiring examples per interface | Tech Lead |
| P0.4 | Prepare rollback scripts | Scripts for Mongo context rollback, storage cleanup, feature toggles | DevOps |
| P0.5 | Team training & comms | Completed 2025-11-11 — docstring FAQ, pre-commit plan, pytest markers delivered in a single-day intensive session | Tech Lead |

> Stage 21_00 activities (P0.1–P0.4) remain on track; training and communications (P0.5) are complete, enabling the team to proceed with one day of focused development to kick off Stage 21_01.

## Phase 1 · Architecture Remediation (Stage 21_01)
Execution order follows the sequential decision captured in `decisions/scope_sequencing.md`.  
Each sub-stage adheres to the template: **tests → implementation → migration → validation**.

### 21_01a · Dialog Context Repository
1. Write tests  
   - Unit: new repository interface using in-memory fake.  
   - Integration: existing Mongo-backed behaviour.
2. Implement interface  
   - Add `DialogContextRepository` protocol + adapters.  
   - Update orchestrator to depend on interface.  
   - Introduce feature flag `USE_DIALOG_CONTEXT_REPO`.
3. Migrate data  
   - Ensure existing documents remain compatible (no schema change).
4. Validate  
   - Run characterization + new tests; monitor latency/DB metrics.

### 21_01b · Homework Review Service
Same template, with added failure-mode tests (HW checker downtime).

### 21_01c · Review Archive Storage
Includes checksum/AV hooks and streaming API. Requires temporary dual-write period:
- Write to both legacy path and new storage.  
- Compare checksums; cut over when stable.

### 21_01d · Use Case Decomposition
Extract collaborators (rate limiter, log pipeline, publisher) with independent tests.

## Phase 2 · Code Quality & Tooling (Stage 21_02)
| Step | Description | Notes |
|------|-------------|-------|
| Q2.1 | Docstring compliance (Option B) | Apply template with pragmatic rules from `docstring_faq.md`. |
| Q2.2 | Function decomposition | Target methods >15 lines, ensure single responsibility. |
| Q2.3 | Pre-commit rollout (Option B) | Fast hooks mandatory; heavy hooks manual + enforced in CI. |
| Q2.4 | CI parity | `make lint`, coverage, security scans incorporated. |

## Phase 3 · Testing & Observability (Stage 21_03)
| Step | Description | Deliverables |
|------|-------------|--------------|
| T3.1 | Coverage uplift | New suites for storage/log pipeline/use case adapters. |
| T3.2 | Security hardening | Checksum enforcement, AV hook optional, secrets handling validated. |
| T3.3 | Observability rollout | Metrics with labels from `observability_labels.md`, updated dashboards, alert tests. |
| T3.4 | Performance validation | Re-run baselines, compare p95/p99 latency, concurrency tests. |

## Phase 4 · Deployment & Rollback
| Step | Description | Requirements |
|------|-------------|--------------|
| D4.1 | Staged rollout | Enable feature flags per component, monitor metrics. |
| D4.2 | Incident drills | Execute rollback scripts, document lessons learned. |
| D4.3 | Final acceptance | Validate functional, quality, operational, business criteria from stage docs. |

## Appendices
- A. Mapping to backlog IDs (ARCH-*, CODE-*, PREP-*).  
- B. Checklist templates (to be generated per sub-stage).  
- C. Links to code examples (to be populated during implementation).


