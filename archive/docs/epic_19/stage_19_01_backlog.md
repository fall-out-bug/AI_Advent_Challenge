# Stage 19_01 · Backlog Draft

| ID | Theme | Priority | Scope | Summary | Notes |
|----|-------|----------|-------|---------|-------|
| EP19-S01-INV-001 | Inventory | P0 | `docs/`, external lecture dirs | Catalogue files (count, size, formats); produce inventory report. | Complete — see `stage_19_01_summary.md` §2 for metrics and exclusion policy. |
| EP19-S01-PRE-002 | Preprocessing | P0 | Markdown/PDF/Code | Define preprocessing pipeline (strip code? handle frontmatter?). Document required libraries (`markdown`, `pypdf`). | Decisions captured in `stage_19_01_summary.md` §3; library choice to be validated in Stage 19_02. |
| EP19-S01-EMB-003 | Embeddings | P0 | LLM API | Confirm embedding model (`text-embedding-3-small` via local API), rate limits, payload structure. | Configuration fixed in `stage_19_01_summary.md` §4; monitor rate limits during prototype run. |
| EP19-S01-STO-004 | Storage | P0 | MongoDB/Redis | Decide collection/index naming, schema (document hash, chunk id, vector). Confirm Redis module availability (Redisearch). | Layout defined in `stage_19_01_summary.md` §5; redis-py dependency pending Stage 19_03. |
| EP19-S01-LGO-005 | Logging & Metrics | P1 | Pipeline instrumentation | Determine metrics/log fields (processing time, chunk count). Plan Prometheus integration. | Baseline requirements noted in `stage_19_01_summary.md` §10; implementation deferred to Stage 19_04 Prometheus integration. |
| EP19-S01-SEC-006 | Security & Retention | P1 | Data storage | Document where datasets/indices stored, retention policy, data hashing. | Policy recorded in `stage_19_01_summary.md` §8; review compliance with ops before go-live. |
| EP19-S01-RFC-007 | Architecture | P1 | Pipeline design | Draft architecture outline/diagram for later stages. | Complete — see `stage_19_02.md` §2 for architecture diagram and narrative. |
| EP19-S01-CLI-008 | Tooling | P2 | CLI skeleton | Outline CLI commands (`index run`, `index status`). | Implemented in Stage 19_03 (`ai-backoffice index run/inspect`). |
