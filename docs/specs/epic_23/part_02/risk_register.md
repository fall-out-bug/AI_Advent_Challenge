# Epic 24 · Risk Register

**Epic:** EP24 – Repository Hygiene & De-Legacy  
**Maintained by:** Tech Lead (cursor_tech_lead_v1)  
**Last Updated:** 2025-11-16

## Risk Register

| ID | Description | Impact | Likelihood | Owner | Mitigation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R24-1 | Refactors break existing production flows | High | Medium | Tech Lead | Use characterisation tests before refactoring, small-scoped PRs per cluster, staged rollout with smoke tests | ⏳ Active |
| R24-2 | Timebox overrun for clusters A–E | Medium | Medium | Tech Lead | Prioritise clusters A/B/C first, defer low-impact items with explicit backlog entries, track progress daily | ⏳ Active |
| R24-3 | Docs drift during refactor | Medium | Medium | Docs Guild | Enforce doc updates as part of DoD for each cluster, run link checks and doc linting in CI | ⏳ Active |
| R24-4 | New architecture boundary violations | High | Low | Architect | Perform architecture-focused reviews for refactor PRs, add simple static checks/grep rules for forbidden imports | ⏳ Active |
| R24-5 | Fixture rollout causes CI instability | Medium | Medium | DevOps | Introduce feature flags / staged rollout, run smoke suites per PR, monitor CI stability | ⏳ Active |
| R24-6 | Channel naming change requires data migration | Medium | Low | Data Services | Provide compat shim + migration script, communicate to doc owners, test migration path | ⏳ Active |
| R24-7 | Refactors span too many modules per PR | Medium | Low | Dev A | Enforce cluster-specific PRs, use acceptance matrix as scope guard, review PR size | ⏳ Active |
| R24-8 | Legacy E2E suites still flaky after refactor | Low | Medium | QA | Archive non-critical suites, add slimmed regression tests aligned with new architecture, document skip rationale | ⏳ Active |
| R24-9 | Test regression during fixture migration | Medium | Medium | Dev A | Run full test suite after each migration batch, create characterization tests before refactoring, maintain baseline metrics | ⏳ Active |

## Risk Mitigation Status

### Active Mitigations
- **R24-1:** Characterisation tests required before refactoring each cluster
- **R24-2:** Daily progress tracking via work_log.md and acceptance_matrix.md
- **R24-3:** Doc updates enforced as DoD requirement per cluster
- **R24-4:** Architecture review required for each refactor PR
- **R24-5:** Feature flags available for fixture rollout
- **R24-6:** Migration script prepared if channel naming changes
- **R24-7:** PR size limits enforced via CI checks
- **R24-8:** E2E suite prioritisation completed
- **R24-9:** Full test suite run after each migration batch, characterization tests created before refactoring, baseline metrics tracked in `test_baseline.md`

## Risk Review Schedule
- **Weekly:** Review active risks during Epic 24 standup
- **Per Cluster:** Risk reassessment during cluster completion review
- **Closure:** Final risk review before Epic 24 closure

---

_Maintained by cursor_tech_lead_v1 · Last updated: 2025-11-16_

