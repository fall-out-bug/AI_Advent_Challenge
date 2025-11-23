# Epic 28 · God Agent “Alfred”

## Purpose
Consolidate every major capability from Days 1–27 into a single **God Agent**
persona (“Alfred”) that behaves like a personal employee: it listens on all
surfaces, plans multi-step work, executes via existing skills (RAG, Butler,
reviewer, ops), and reports results with observability and guardrails.

## Context
- Day 25 already introduced *Alfred-style* personalisation for the Butler bot.
- Day 23 delivered the observability/metrics stack; Day 24 added voice control.
- Day 21/22/23/24/25 + epics 18–27 produced reusable services (RAG, reviewer,
  planner, MCP tools, deployment scripts, consensus workflow).
- The repo now exposes compact role prompts and a shared consensus contract
  (`docs/roles/consensus_architecture.json`). Epic 28 should consume these
  assets instead of reinventing them.

## Goals & Success Metrics
| # | Goal | Metric |
|---|------|--------|
| G1 | Single entrypoint “Alfred” inside Telegram (text + voice) that handles end-to-end flows | 100% of user interactions go through the Butler/Telegram bot |
| G2 | Autonomous planning that maps a natural request to a task graph and executes via skills | ≥3 task types (concierge/research/builder/reviewer) run without manual glue |
| G3 | Unified memory/profile + artefact timeline reused across interactions | Persona + working memory retrieved in <150ms and referenced in responses |
| G4 | Observability + safety guardrails remain intact | Prometheus exports new `god_agent_*` metrics; veto/escalation flow wired |

## Scope
### Must
1. **Unified Intent Router**: classify user request → choose execution mode
   (concierge reply, research, build, review, ops). Intent model must reuse the
   RAG knowledge base and structured prompts from previous days.
2. **Task Graph Planner**: break requests into ordered steps (plan, research,
   build, review, deploy) with explicit acceptance checks. Planner should invoke
   the consensus workflow when a step needs multi-agent scrutiny.
3. **Skill Graph**: wrap existing subsystems as skills:
   - Butler/concierge (Day 25 persona pipeline)
   - Research/RAG (Days 20–22)
   - Builder (Day 13 Butler refactor + Day 16 memories)
   - Reviewer (Day 14 multi-pass + Day 17 platform)
   - Ops/Deploy (Days 23–24 + shared infra playbook)
4. **Memory Fabric**: merge user profile, interaction memory, and artefact
   timeline (epics 24–25). Provide APIs for planner/skills to read & write.
5. **Observability + Safety**: instrument every task step with Prometheus +
   structured logs; enforce veto rules from `docs/roles/consensus_architecture.json`.
6. **Documentation & Runbooks**: publish how Alfred is exposed via the Butler/Telegram bot (text + voice), how to enable/disable skills, and how to escalate.

### Should
- Background jobs: scheduled digests, proactive alerts (e.g., remind user of
  unresolved tasks, share metrics).
- Plugin/skill registry: declarative config that maps `skill_id` → adapter so
  future capabilities can be added without touching the core orchestrator.
- Optional operator CLI/TUI for debugging (non-user facing) that mirrors
  Telegram conversations, primarily for engineers.

### Out of Scope
- New LLM features outside existing stack (still rely on local Qwen/Claude
  endpoints).
- Cloud SaaS dependencies (stick to shared infra).
- Production mobile apps (Telegram + CLI/voice are enough for Day 28).

## Acceptance Criteria
- [ ] `GodAgentSpec` (this doc) approved by Analyst/Architect/Tech Lead.
- [ ] Domain layer contains contracts for `Intent`, `TaskPlan`, `TaskStep`,
      `Skill`, `SkillResult`, `MemorySnapshot`, `SafetyViolation`.
- [ ] Application layer exposes:
      - `IntentRouterService`
      - `PlanCompilerService`
      - `GodAgentOrchestrator` with pause/resume/cancel + consensus hooks.
- [ ] Infrastructure layer provides adapters for:
      - Persona/memory repositories (reuse Day 25 Mongo models).
      - RAG client + embedding index.
      - MCP/reviewer tools + CI scripts.
      - Voice pipeline (Whisper) + Telegram bot.
- [ ] Presentation layer reuses Butler surfaces but routes through Alfred.
- [ ] Observability:
      - Metrics: `god_agent_tasks_total`, `god_agent_plan_duration_seconds`,
        `god_agent_veto_total`, `god_agent_skill_latency_seconds`.
      - Traces/logs include `task_id`, `skill_id`, `plan_step`.
- [ ] Smoke tests cover at least one flow per skill (concierge greetings,
      research answer with citations, code change + review, ops check).

## Architecture Overview
```
Input Surface (CLI / Telegram / Voice)
        │
        ▼
  Intent Router ──> Dispatch Decision
        │                  │
        │                  ├── Concierge Skill
        │                  ├── Research Skill (RAG)
        │                  ├── Builder Skill (plan→code)
        │                  ├── Reviewer Skill (multi-pass)
        │                  └── Ops Skill (deploy/metrics)
        ▼
  Plan Compiler
        │
        ▼
  Execution Engine ── Memory Fabric ── Observability
        │
        ▼
   Consensus Bridge (invokes agent prompts when needed)
```

### Domain Layer
- `GodAgentProfile`: persona, language, permissions, preferred skills.
- `Intent` + `IntentConfidence`: output of routing classification.
- `TaskPlan` → list of `TaskStep` with dependencies & acceptance gates.
- `SkillContract`: declares inputs, outputs, veto conditions.
- `MemorySnapshot`: user profile + short-term summary + artefact refs.
- `SafetyViolation`: ties into veto rules (scope expansion, layer violation,
  security risk, etc.).

### Application Layer
1. **IntentRouterService**
   - Input: `UserMessage` (text, voice transcript, CLI command).
   - Output: `(Intent, confidence, suggested_skills)`.
   - Implementation: combine keywords, embeddings, and prior tasks stored in
     memory. Falls back to concierge if confidence < threshold.
2. **PlanCompilerService**
   - Converts `(Intent, MemorySnapshot)` into a DAG:
     - Step templates (e.g., `research`, `draft`, `review`, `deploy`).
     - Each step knows which Skill adapter to call.
     - Annotated with acceptance criteria + rollback instructions.
3. **GodAgentOrchestrator**
   - Executes plan steps sequentially/parallel where allowed.
   - Publishes events (`TASK_STARTED`, `STEP_DONE`, `VETO_RAISED`).
   - Automatically hands off to `ConsensusBridge` when a step requests
     multi-agent validation (e.g., architecture change).
4. **ConsensusBridge**
   - Reuses `docs/roles/consensus_architecture.json` to run Analyst/Architect/
     Tech Lead flows when needed (mostly asynchronous; Alfred waits for verdict).
5. **MemoryFabricService**
   - Aggregates persona (Day 25), conversation summary, RAG hits, and latest
     artefacts (code diffs, review notes).
   - Provides TTL/compaction so Alfred stays within token budgets.

### Infrastructure Layer
- **LLM Clients**: local Qwen (chat) + optional Claude for planning tasks.
- **RAG**: Day 20–22 ingestion pipeline + search API (embedding-based).
- **Code Tools**: MCP reviewer, test runner scripts, `scripts/quality/*`.
- **Voice**: Day 24 Whisper pipeline for STT; optional TTS for responses.
- **Messaging**: Telegram bot handlers + CLI wrapper share same orchestrator.
- **Storage**: Mongo (users/memory/plans), Redis (short-term caches),
  object store (artefact attachments).
- **Observability**: Prometheus metrics, Loki logs, Grafana dashboards.

### Presentation Layer
- Telegram Alfred bot (existing Butler bot routes all text/voice into Alfred).
- Voice is delivered via Telegram voice notes → Day 24 transcription → Alfred response.
- Optional operator CLI/TUI is strictly for debugging/admin and is not a user entrypoint.

## Workstreams
1. **Domain & Contracts**
   - Deliver new value objects/interfaces.
   - Update docs in `docs/roles/README.md` to mention Alfred orchestrator.
2. **Memory Fabric + Persona Merge**
   - Extend Day 25 repositories with task timeline + artefact references.
   - Add summarisation job for long histories.
3. **Intent Routing & Planner**
   - Implement router (ML-lite + rule hybrid).
   - Build plan templates for at least 4 skill chains.
4. **Skill Adapters**
   - Concierge: wrap existing personalised Butler flow.
   - Research: connect to QA/RAG pipeline with citations.
   - Builder: call code-gen use case + tests.
   - Reviewer: multi-pass MCP reviewer integration.
   - Ops: run shared infra scripts, fetch metrics, operate deployments.
5. **Consensus Bridge + Safety**
   - When plan step flagged as critical, trigger multi-agent consensus files
     under `docs/specs/epic_28/consensus/`.
6. **Presentation & Voice**
   - CLI + Telegram integrated with new orchestrator.
   - Voice transcription piping into same API.
7. **Observability & QA**
   - Metrics/logging/tracing coverage.
   - Smoke + integration suites per skill.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Planner over-schedules or loops | Runaway tasks | Hard cap on plan depth + watchdog timers per step |
| Skills diverge from underlying subsystems | Drift, regressions | Skill adapters call existing use cases; unit tests reuse prior fixtures |
| Memory bloat | Token + storage issues | Summary compression + TTL policies |
| Consensus integration stalls flows | Latency | Async queue + notifications; only critical steps trigger full consensus |

## Constraints
- **Security/Compliance**: stay local (Mongo, Prometheus, Qwen). No external SaaS.
- **Infra/Performance**:
  - Response target < 5s for concierge tasks, < 30s for multi-step flows.
  - Planner must respect token budgets defined in role prompts.
  - Reuse `docs/operational/shared_infra.md` service matrix.

## References
- `docs/specs/epic_25/*` — personalised Butler (persona, memory).
- `docs/specs/epic_24/*` — voice pipeline.
- `docs/specs/epic_23/*` — observability stack.
- `docs/specs/epic_21/*` — RAG++ architecture and clean architecture refactor.
- `docs/specs/epic_20/*` — RAG vs. non-RAG answering baseline.
- `docs/specs/epic_14/*`, `epic_17/*` — multi-pass reviewer + MCP platform.
- `docs/roles/consensus_architecture.json` — consensus + veto schema.
- `docs/roles/*/prompt.json` — skill prompts when Alfred triggers agent mode.
