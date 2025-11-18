<<<<<<< HEAD
# Tech Lead Examples

- Store plan stage tables (`stages.md`) with DoD and evidence samples.
- Include risk register extracts plus mitigation follow-up notes.
- Provide CI pipeline mappings (command snippets, coverage reports).
- Capture handoff checklists and resolved feedback summaries.
=======
# Tech Lead Role Examples

Detailed examples demonstrating staged planning, CI/CD gates, risk management, and deployment strategies.

---

## Examples

### Staged Planning with CI/CD Gates
**File:** `staged_planning_cicd_gates.md`
**Contains:** 8-stage plan, CI gate matrix, risk register
**Metrics:** 40 days, 8 CI gates, 3 risks identified

### Risk Management
**File:** `risk_management.md`
**Contains:** Risk register template, severity matrix, mitigation strategies
**Example:** 3 risks (external API, DB migration, compliance)

### Deployment Strategy
**File:** `deployment_strategy.md`
**Contains:** Canary rollout (10%→50%→100%), blue-green alternative
**Metrics:** < 5min rollback, 24h monitoring window

### Developer Handoff
**File:** `handoff_to_developer.md`
**Contains:** Complete handoff JSON with stages, commands, CI gates
**Quality:** All DoD defined, rollback plan included

---

## Matrix

| Example | Key Metric | Benefit |
|---------|------------|---------|
| Staged Planning | 8 stages, 40 days | Clear execution path |
| Risk Management | 3 risks mitigated | Proactive problem solving |
| Canary Deployment | 0% downtime | Safe production rollout |
| Developer Handoff | 100% checklist complete | Developer ready to start |

---

## Related
- Capabilities: `../day_capabilities.md`
- RAG Queries: `../rag_queries.md`
- Handoff Contracts: `../../operational/handoff_contracts.md`
>>>>>>> origin/master
