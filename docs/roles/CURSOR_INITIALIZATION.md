<<<<<<< HEAD
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
=======
# Cursor Agent Initialization

## How to Use This Guide

When you start a Cursor agent, load this sequence:

1. **Load core role definition**
   - File: `docs/roles/<role>/role_definition.md` (from agent_workflow.md)
   - This is STATIC and doesn't change

2. **Load current capabilities**
   - File: `docs/roles/<role>/day_capabilities.md`
   - This UPDATES with each new Epic
   - Shows which Days/Epics have been completed and what you can now do

3. **Load RAG queries**
   - File: `docs/roles/<role>/rag_queries.md`
   - These are the specific MongoDB queries or document searches you should use
   - Example: Analyst queries "previous requirements similar to X"

4. **Load recent examples**
   - Files: `docs/roles/<role>/examples/epic_*.md`
   - Use the most recent epic as a template for your work

5. **Check operational context**
   - File: `docs/operational/context_limits.md` (max tokens, compression strategy)
   - File: `docs/operational/handoff_contracts.md` (input/output formats)
   - File: `docs/operational/shared_infra.md` (MongoDB, LLM API, Prometheus)

## Example: Starting Analyst Agent on Day 23

1. Load: `docs/roles/analyst/role_definition.md` (core responsibilities)
2. Load: `docs/roles/analyst/day_capabilities.md` (now includes Day 22 RAG + Day 23 Observability!)
3. Load: `docs/roles/analyst/examples/epic_22_rag_example.md` (latest example)
4. Check: `docs/operational/context_limits.md` (token budget for this epic)
5. Ready: Analyst agent can now:
   - Gather requirements (Day 1-3)
   - Compress long dialogs (Day 15)
   - Query RAG for similar requirements (Day 22)
   - Self-observe and log decisions (Day 23) ← NEW!
>>>>>>> origin/master
