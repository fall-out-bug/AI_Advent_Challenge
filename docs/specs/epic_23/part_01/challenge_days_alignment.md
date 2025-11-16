# Epic 23 · Challenge Days Alignment

Purpose:
    Map AI Challenge Day requirements to the actual implementation in this
    repository and highlight remaining gaps.

## Day-by-Day Alignment

| Day | Summary of Requirement | Implementation (Files/Modules) | Gaps / Risks |
| --- | ---------------------- | ------------------------------- | ------------ |
| 1 | Basic agent + tool call | `src/domain/agents/*`, `src/presentation/api/*`, `src/presentation/mcp/server.py`, CLI and bot in `src/presentation/cli/*`, `src/presentation/bot/*` | No minimal "hello world" demo; only full multi-agent architecture. |
| 2 | Structured outputs, parseable responses | DTOs in `src/application/dtos/*`, MCP tool schemas `src/presentation/mcp/tools/*`, handoff JSON formats in `docs/operational/handoff_contracts.md` | Schemas are implicit in code; newcomer-facing schema overview docs could be clearer. |
| 3 | Stopping conditions and dialog result | `docs/roles/analyst/day_capabilities.md#day-3`, `docs/roles/analyst/examples/day_3_conversation_stopping.md`, dialog entities in `src/domain/entities/conversation.py` | Clarity/stop logic is documented but not exposed as a single, clearly named use case. |
| 4 | Temperature tuning | `docs/roles/analyst/day_capabilities.md#day-4`, LLM config in `src/infrastructure/llm/*`, RAG prompt assembly in `src/application/rag/prompt_assembler.py` | Concrete temperature values live in configs; no single doc shows "0/0.7/1.2" mapping for all roles. |
| 5 | Model variants and comparison | `docs/specs/agents/MODELS.md`, `src/domain/models/*`, `src/infrastructure/llm/*`, `scripts/quality/benchmark/run_benchmark.py` | HF-style "early/mid/late" comparison is not explicitly reported; covered indirectly via EP05 benchmarks. |
| 6 | Chain of Thought reasoning | `docs/roles/analyst/day_capabilities.md#day-6`, prompts in `src/domain/agents/prompts.py`, EP21 design docs | CoT vs non-CoT comparison results live mostly in docs, not in automated tests. |
| 7 | Multi-agent interaction / peer review | `src/application/orchestrators/multi_agent_orchestrator.py`, multi-role agents in `src/domain/agents/*`, `docs/roles/analyst/day_capabilities.md#day-7` | EP23 does not yet add a fresh example of Analyst↔Reviewer loop using new observability data. |
| 8 | Token budgeting and compression | `docs/roles/analyst/day_capabilities.md#day-8`, `#day-15`, `docs/operational/context_limits.md`, examples in `docs/roles/analyst/examples/day_8_token_budgeting.md` and `day_15_compression.md` | Core logic present but no tiny CLI/demo showing short/long/overflow behaviour for teaching purposes. |
| 9 | MCP connection and tool listing | MCP HTTP server `src/presentation/mcp/http_server.py`, metrics `src/infrastructure/monitoring/mcp_metrics.py`, MCP usage docs | Minimal script "list MCP tools" not extracted as a separate example; functionality is available via server. |
| 10 | First MCP tool | MCP tools in `src/presentation/mcp/tools/*`, EP02 MCP inventory docs | No dedicated "first tool" tutorial; only production-grade tools and tests. |
| 11 | Scheduler + MCP (24/7 summary) | Workers `src/workers/*` (schedulers, summary), health tests `scripts/quality/test_review_system.py`, EP03/EP11 specs | Day 11 capability is implemented but not explicitly cross-referenced from challenge days in user-facing docs. |
| 12 | Composition of MCP tools | Use cases `src/application/use_cases/*` (digests, summaries), MCP tool chains in application layer, `docs/roles/analyst/day_capabilities.md#day-12` | No single "search→summarise→save" walkthrough; composition scattered across use cases. |
| 13 | Real environment / Docker | `docs/operational/shared_infra.md`, `scripts/infra/start_shared_infra.sh`, `scripts/ci/bootstrap_shared_infra.py`, `make day-12-up`, integration tests `tests/integration/shared_infra/*` | Rich environment exists; no minimal "start one container and execute X" teaching snippet. |
| 14 | Project-wide code analysis | Multipass reviewer (`packages/multipass-reviewer/*`), EP01/EP21 docs, MCP code-analysis tools in `src/presentation/mcp/tools/*` | Day 14 scenario not explicitly referenced in user guide as an example session. |
| 15 | Dialog compression | `docs/roles/analyst/day_capabilities.md#day-15`, `docs/roles/analyst/examples/day_15_compression.md`, compression in context/RAG flows | Compression used, but not exposed as a simple "every N messages" utility with its own tests. |
| 16 | External memory | Mongo-backed repositories `src/infrastructure/database/*`, `docs/operational/shared_infra.md#mongodb`, `docs/roles/analyst/day_capabilities.md#day-16` | SQLite/JSON-style examples from the challenge are replaced by Mongo; no small standalone persistence demo. |
| 17 | Data processing pipeline | Use cases in `src/application/use_cases/*`, RAG pipeline in `src/application/rag/use_case.py`, dataset prep scripts `scripts/quality/analysis/*` | Pipelines exist but are not documented as a Day 17 "mini pipeline" example. |
| 18 | Real-world task | EP00–EP06 summary `docs/specs/epic_18/epic_18.md`, EP05 benchmark pipeline, EP02 CLI/Telegram flows | Multiple real tasks exist; Day 18 is not explicitly tied to a single showcase scenario. |
| 19 | Document indexing | `src/domain/embedding_index/*`, `src/application/embedding_index/*`, `src/infrastructure/vector_store/*`, `docs/specs/epic_20/epic_20.md`, `docs/roles/analyst/day_capabilities.md#day-19` | Indexing implemented, but EP19 remains Planned in `docs/specs/progress.md`; no fresh EP19-specific run/report this program. |
| 20 | First RAG query | `src/application/rag/use_case.py`, `scripts/rag/day_20_demo.py`, `docs/specs/epic_20/epic_20.md` | RAG mechanics present; EP20 not yet marked as completed in progress tracker. |
| 21 | Reranking and filtering | Rerank metrics `src/infrastructure/metrics/rag_metrics.py`, config `config/retrieval_rerank_config.yaml`, `scripts/rag/day_21_demo.py`, EP21 docs | Reranking is wired, but no consolidated Day 21 report comparing quality before/after in this programme. |
| 22 | Citations and sources | `docs/roles/analyst/day_capabilities.md#day-22`, `docs/roles/analyst/examples/day_22_rag_citations.md`, `docs/roles/analyst/rag_queries.md` | Pattern implemented at doc level; not yet enforced as a mandatory behaviour for specific RAG endpoints with tests. |
| 23 | Free day → Observability & Benchmarks | Epic 23 files under `docs/specs/epic_23/*`, benchmark data in `data/benchmarks/*`, scripts `scripts/quality/analysis/export_*.py`, `scripts/quality/benchmark/run_benchmark.py`, metrics in `src/infrastructure/metrics/*`, infra bootstrap scripts | Core Epic 23 goals met; Day 23 result not yet summarised back into `docs/challenge_days.md` as a narrative of "what we did". |


