# Stage 19_01 · Backlog Draft

| ID | Theme | Priority | Scope | Summary | Notes |
|----|-------|----------|-------|---------|-------|
| EP19-S01-INV-001 | Inventory | P0 | `docs/`, external lecture dirs | Catalogue files (count, size, formats); produce inventory report. | Include markdown, notebooks, PDF, code files. |
| EP19-S01-PRE-002 | Preprocessing | P0 | Markdown/PDF/Code | Define preprocessing pipeline (strip code? handle frontmatter?). Document required libraries (`markdown`, `pypdf`). | Verify licensing. |
| EP19-S01-EMB-003 | Embeddings | P0 | LLM API | Confirm embedding model (`text-embedding-3-small` via local API), rate limits, payload structure. | Capture in requirements doc. |
| EP19-S01-STO-004 | Storage | P0 | MongoDB/Redis | Decide collection/index naming, schema (document hash, chunk id, vector). Confirm Redis module availability (Redisearch). | Fallback to local FAISS if Redis offline. |
| EP19-S01-LGO-005 | Logging & Metrics | P1 | Pipeline instrumentation | Determine metrics/log fields (processing time, chunk count). Plan Prometheus integration. | Align with EP03 metrics. |
| EP19-S01-SEC-006 | Security & Retention | P1 | Data storage | Document where datasets/indices stored, retention policy, data hashing. | Include in operations guide. |
| EP19-S01-RFC-007 | Architecture | P1 | Pipeline design | Draft architecture outline/diagram for later stages. | Provide to Stage 19_02. |
| EP19-S01-CLI-008 | Tooling | P2 | CLI skeleton | Outline CLI commands (`index run`, `index status`). | Implement later stages. |
