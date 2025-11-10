# Epic 04 · Known Issues and Deferred Follow-ups

Last updated: 2025-11-10

## 1. MongoDB-Backed Test Suites

- **Suites impacted:** `src/tests/e2e/test_full_workflow.py`, `src/tests/infrastructure/test_task_repository.py`, `src/tests/presentation/mcp/test_digest_tools.py`
- **Current behaviour:** Require shared infra plus `MONGODB_URL="mongodb://admin:<pwd>@127.0.0.1:27017/butler_test?authSource=admin"`. Without credentials they skip with `"MongoDB authentication required"`.
- **Follow-up:** Provide CI fixture/profile that sources `.env.infra` automatically (Stage 04_03 sign-off item). Long-term, encapsulate connection bootstrap in test utilities.

## 2. MCP Performance Benchmarks

- **Tests:** `TestPerformanceMetrics.test_calculator_tool_latency`, `TestPerformanceMetrics.test_token_counting_performance`
- **Status:** Marked `xfail` (Stage 04_03) because latency budgets (<0.5s, <0.2s) no longer realistic after modular reviewer/MCP refactors.
- **Follow-up:** Observability backlog (Epic 05) to recalibrate SLAs or move benchmarks to load-testing harness.

## 3. Summarizer Locale Variance

- **Test:** `test_summarize_posts_empty_list`
- **Status:** Accepts both English and Russian fallback text (`"No posts to summarize."` / `"Нет постов для саммари."`)
- **Follow-up:** Align summarizer responses with locale-aware configuration (future internationalisation work).

## 4. Legacy End-to-End Coverage

- **Context:** Reminder/legacy CLI flows archived; large portions of legacy E2E suite removed or skipped.
- **Follow-up:** Stage 04_03 closure to capture new CLI/backoffice scenarios; Epic 05 will introduce deterministic smoke suite once shared infra orchestration is automated.

---

All outstanding issues are tracked in Stage 04_03 closure plan. Refer to this file when preparing stakeholder sign-off and post-epic handover.
