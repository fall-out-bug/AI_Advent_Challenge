## Cursor Agent Initialization · Стартовый Маршрут

### Purpose / Цель
Provide a single entry point for autonomous and paired Cursor agents to load
context, understand current Epic focus, and navigate living documentation.

### Quick Start Checklist
- Load `docs/specs/process/agent_workflow.md` to grasp orchestration.
- Identify your role folder under `docs/roles/` and open `role_definition.md`.
- Review `day_capabilities.md` for the current epic window (Дни 1‑22 baseline).
- Open `rag_queries.md` for data retrieval patterns and context refresh.
- Check `docs/operational/context_limits.md` for token and memory budgets.
- Confirm hand-off formats in `docs/operational/handoff_contracts.md`.
- Sync with latest epic notes under `docs/epics/`.

### Daily Boot Sequence
1. **Sync context** – run role-specific RAG queries, capture deltas in worklog.
2. **Review responsibilities** – align with `role_definition.md` DoD checkpoints.
3. **Plan contributions** – cross-reference `day_capabilities.md` Foundations.
4. **Execute & log** – follow TDD, Clean Architecture, and repo-wide rules.
5. **Prepare hand-off** – format outputs per `handoff_contracts.md`.

### Navigation Map
- Roles: `docs/roles/<role>/`
- Operational Guides: `docs/operational/`
- Epics Timeline: `docs/epics/`
- Architecture Foundations: `docs/specs/architecture.md`
- Repository Onboarding (RU): `README.ru.md`

### Notes
- Keep documents concise (≤88 chars/line) and bilingual only where value added.
- Update relevant `day_capabilities.md` after each epic/day to keep the system
  живым (“alive”).
- Report missing context via `docs/epics/<epic>/reviews/` feedback loops.

### Review Checklist
- [ ] Links resolve to existing files.
- [ ] Role folders contain required templates.
- [ ] Operational docs reflect latest token & hand-off guidance.
- [ ] Epics directory aligns with current release cadence.

