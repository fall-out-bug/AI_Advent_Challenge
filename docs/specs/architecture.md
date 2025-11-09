# Architecture Specification

## 1. Architectural Vision
The repository adopts Clean Architecture with Domain-Driven Design boundaries.
Business rules live in `src/domain`, application orchestration in
`src/application`, infrastructure integrations in `src/infrastructure`, and
interfaces/presentation layers in `src/presentation` plus external packages.
The modular reviewer package (`packages/multipass-reviewer`) remains the
canonical implementation for code review automation.

## 2. Layer Responsibilities
| Layer | Responsibilities | Allowed Dependencies |
|-------|------------------|-----------------------|
| Domain (`src/domain`) | Entities, value objects, pure logic | None (pure Python) |
| Application (`src/application`) | Use cases, services, orchestration | Domain |
| Infrastructure (`src/infrastructure`) | DB clients, external services, logging, metrics | Application (via interfaces), third-party libs |
| Presentation (`src/presentation`) | APIs, CLI, MCP tools, bot interfaces | Application, Infrastructure adapters |

## 3. Cross-Cutting Modules
- `shared/` editable SDK shared across projects.
- `packages/multipass-reviewer/` reusable reviewer package with its own strict
  linting/testing.
- `scripts/` operational helpers (health checks, migrations).

## 4. Key Architectural Decisions
- **Modular Reviewer First**: all code review flows route through
  `ModularReviewService`; legacy agents remain archived.
- **Multi-Pass Expansion**: reviewer pipeline includes runtime log analysis
  (Pass 4) alongside architecture, component, and synthesis passes.
- **Structured Logging**: `StructuredLogger` wraps stdlib logging so callers can
  pass contextual kwargs; logs flow to shared Prometheus/Grafana via exporters.
- **Infra via Adapters**: Use dependency injection to bridge between application
  services and external systems (Mongo, LLM, Prometheus).
- **Feature Flags**: `USE_MODULAR_REVIEWER`, `use_new_summarization`, etc. must
  be documented in ops guide and default to safe values.
- **Summarisation Stack**: adaptive/map-reduce summarizers with semantic
  chunking and LLM-as-judge evaluation underpin digest features and
  fine-tuning workflows.

## 5. Gaps Identified (to be confirmed in Stage 00_01)
- MCP/Bot modules still rely on legacy expectations (e.g., English vs Russian
  copy, missing orchestrator dependencies).
- Tests assume unauthenticated Mongo; needs harmonisation with shared infra.
- Extensive lint violations in `src/infrastructure`, `src/presentation`, and
  `src/tests` require staged cleanup.

## 6. Next Steps
- Complete inventory to fill "Gaps" table with precise modules.
- Derive epics for reviewer hardening, MCP consolidation, infra observability,
  and archive cleanup.
