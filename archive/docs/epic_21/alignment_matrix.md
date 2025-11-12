# Epic 21 · Alignment Matrix

This matrix links Epic 21 remediation tasks to the guiding specifications:
- `.cursor/rules/cursorrules-unified.md`
- `docs/specs/architecture.md`
- `docs/specs/specs.md`
- `docs/specs/operations.md`

## Layer & Rule Coverage
| Area | Spec Reference | Observed Gap | Planned Stage Task |
|------|----------------|--------------|--------------------|
| Domain isolation | `architecture.md` §2, Clean Architecture table | Domain modules import infrastructure clients (`ButlerOrchestrator`, `HomeworkHandler`, `ChannelScorer`) | Stage 21_01 · ARCH-21-01/02 |
| Use case orchestration | `specs.md` §1.1–1.3, `.cursorrules` Chief Architect | Monolithic `ReviewSubmissionUseCase` helper methods mixing orchestration, logging, persistence | Stage 21_01 · ARCH-21-04; Stage 21_02 · CODE-21-01 |
| Presentation IO boundaries | `.cursorrules` Python Zen & Security, `operations.md` §2–3 | `review_routes.create_review` writes archives directly to disk without shared storage abstraction | Stage 21_01 · ARCH-21-03; Stage 21_03 · SEC-21-02 |
| Docstring & typing | `.cursorrules` Python Zen Writer, Technical Writer | Public APIs (e.g., `ContextManager`) lack mandated docstring template sections | Stage 21_02 · CODE-21-03 |
| Function size limits | `.cursorrules` AI Reviewer | Oversized helpers (`_append_log_analysis`, `_persist_report`) exceed 15-line guideline | Stage 21_02 · CODE-21-01 |
| Security posture | `.cursorrules` Security Reviewer, `operations.md` §1–3 | Archive storage lacks checksum/scan hooks; env sourcing not centralised | Stage 21_03 · SEC-21-02 |
| Observability | `operations.md` §4, `specs.md` §4 | Prometheus/Grafana configs not mapped to new services | Stage 21_03 · OBS-21-03 |
| Testing strategy | `.cursorrules` QA/TDD Reviewer, `specs.md` §2 | No targeted tests for upcoming storage/log adapters | Stage 21_03 · TEST-21-01 |

## Risk Register Snapshot
| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| Domain uses infra adapters directly | High | Introduce protocols + DI in Stage 21_01 | Domain/App |
| Docs fall out of sync during refactor | Medium | Update docstrings + README after each module move (Stage 21_02) | Docs Lead |
| Storage refactor delays deployments | Medium | Provide feature flag + migration plan in Stage 21_03 | Infra |
| Monitoring debt masks regressions | High | Refresh dashboards/alerts during Stage 21_03 before rollout | DevOps |

## Coordination Notes
- Sync with EP01 reviewer hardening to avoid diverging repository interfaces.
- Notify ops team before introducing new environment variables or storage paths.
- Ensure QA adds new suites to CI matrix once Stage 21_02 helpers stabilize.


