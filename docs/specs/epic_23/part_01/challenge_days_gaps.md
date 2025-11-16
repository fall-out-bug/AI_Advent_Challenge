# Epic 23 · Challenge Days 1–22 Gaps

Purpose:
    Track remaining discrepancies between `docs/challenge_days.md` (Days 1–22)
    and the current repository implementation, to be addressed in or after
    Epic 23.

## Summary of Gaps by Day

- **Day 1 – Basic Agent Demo**
  - **Expectation:** Minimal chat agent that calls a single tool.
  - **Reality:** Only full multi-agent/multi-role implementation is visible
    (`src/domain/agents/*`, API/MCP/CLI/bot).
  - **Gap:** No tiny "hello world" agent example (one file + one tool) for
    onboarding and challenge-day validation.

- **Day 2 – Output Schema Visibility**
  - **Expectation:** Clearly defined output format, easy to parse.
  - **Reality:** DTOs and Pydantic models exist across layers, but schemas are
    scattered.
  - **Gap:** No short, centralized doc that shows 1–2 canonical response
    schemas mapped directly to Day 2 narrative.

- **Day 3 – Stopping Condition as First-Class Use Case**
  - **Expectation:** Model knows when to stop gathering and returns a result
    (e.g. requirements pack).
  - **Reality:** Patterns documented for Analyst (clarity_score, stopping), but
    logic is embedded inside multi-agent flows.
  - **Gap:** No single public "Day 3 stopping" use case or CLI that demonstrates
    conversation → stop → JSON output end-to-end.

- **Day 4 – Temperature Examples**
  - **Expectation:** Side-by-side comparison for T=0 / 0.7 / 1.2 with guidance.
  - **Reality:** Temperature usage hidden in configs and prompt assembly; no
    explicit Day 4 comparison artefact.
  - **Gap:** No simple script or notebook that runs *the same prompt* at three
    temperatures and records outputs.

- **Day 5 – Model Comparison Report**
  - **Expectation:** Compare models (early/mid/late), time, tokens, cost.
  - **Reality:** Model routing and benchmarks exist, but not structured as a
    "Day 5" comparison story.
  - **Gap:** No concise report or example mapping Day 5 requirements to actual
    benchmark runs and summarised conclusions.

- **Day 6 – CoT vs Non-CoT Evidence**
  - **Expectation:** Two outputs (with/without CoT) and correctness analysis.
  - **Reality:** CoT prompting is applied in several places, but comparison is
    only described narratively in role docs.
  - **Gap:** No test or example showing the same task solved twice with metrics
    (accuracy/clarity) to demonstrate CoT benefit.

- **Day 7 – Peer Review Example with Current Stack**
  - **Expectation:** Agent 2 reviews Agent 1 output.
  - **Reality:** Multi-agent reviewer exists, but latest EP23 observability
    context is not used in a fresh Analyst↔Reviewer example.
  - **Gap:** No up-to-date example that ties Day 7 peer review to new metrics
    and logs from Epic 23.

- **Day 8 – Token Budget Demo**
  - **Expectation:** Short vs long vs overflow queries with token counts and
    compression.
  - **Reality:** Token budgeting & compression are implemented in patterns, not
    as a standalone educational demo.
  - **Gap:** No small CLI that prints token usage and demonstrates truncation /
    summarisation decisions for a single role.

- **Day 9 – MCP Tool Listing Demo**
  - **Expectation:** Minimal code that connects to MCP and lists tools.
  - **Reality:** MCP server is fully implemented; listing is available via HTTP,
    but not showcased as a Day 9 example.
  - **Gap:** No self-contained script or doc snippet "how to call /tools and
    interpret the response" linked from challenge docs.

- **Day 10 – First MCP Tool Tutorial**
  - **Expectation:** One simple MCP tool wired end-to-end.
  - **Reality:** Many production MCP tools exist with tests.
  - **Gap:** No beginner-level tutorial that walks through creation, registration
    and invocation of a single trivial tool.

- **Day 11 – Scheduler + Summary Story**
  - **Expectation:** 24/7 agent issuing summaries periodically.
  - **Reality:** Scheduler/workers implement this pattern, but not explicitly
    tied back to Day 11 narrative.
  - **Gap:** No short user-facing story or doc page that says "this is our Day
    11 implementation" and shows example outputs.

- **Day 12 – Composed Tool Pipeline Example**
  - **Expectation:** search→summarise→save pipeline via tools.
  - **Reality:** Pipelines exist in application/use cases, but are spread across
    several modules.
  - **Gap:** No single, documented pipeline minimal example that clearly matches
    the Day 12 description.

- **Day 13 – Minimal Environment Demo**
  - **Expectation:** Agent interacts with a real container/emulator.
  - **Reality:** Full shared infra (Mongo, Prometheus, Grafana, LLM, Loki) and
    bootstrap scripts exist.
  - **Gap:** No minimal "one container + one check" demo aligned with Day 13
    text (current materials may be overwhelming).

- **Day 14 – Project Analysis Walkthrough**
  - **Expectation:** Agent analyses a large project and reports structure/bugs.
  - **Reality:** Multipass reviewer does this, but not linked as a Day 14
    walkthrough.
  - **Gap:** No single scenario doc that says: "run X command to perform a Day
    14-style project analysis on this repo."

- **Day 15 – Simple Compression Utility**
  - **Expectation:** Compress dialog every N messages and compare quality/tokens.
  - **Reality:** Compression patterns integrated into agents/RAG, with examples
    in docs.
  - **Gap:** No standalone utility (module or CLI) that can be pointed at an
    arbitrary transcript and produce before/after metrics.

- **Day 16 – Lightweight External Memory Demo**
  - **Expectation:** SQLite/JSON persistence with cross-run continuity.
  - **Reality:** MongoDB used as primary external memory with robust adapters.
  - **Gap:** No lightweight, challenge-style example (e.g. small JSON/SQLite
    store) that mirrors the exact Day 16 description.

- **Day 17 – Mini Data Pipeline Example**
  - **Expectation:** Simple pipeline (clean→summary→query docs).
  - **Reality:** Several production pipelines exist, but not marketed as "Day
    17 example".
  - **Gap:** No concise, documented end-to-end pipeline that maps directly to
    the text of Day 17.

- **Day 18 – Named Real-World Task**
  - **Expectation:** Clearly stated real-world task + app that addresses it.
  - **Reality:** Multiple epics cover real-world tasks (observability,
    benchmarks, MCP, CLI), but Day 18 is not explicitly anchored to a specific
    one.
  - **Gap:** No single "Day 18 task" summary describing which Epic/feature is
    considered the answer to this challenge.

- **Day 19 – Indexing Epic Closure**
  - **Expectation:** Document indexing pipeline, local index.
  - **Reality:** Indexing code and infrastructure exist; EP19 in
    `docs/specs/progress.md` still Planned.
  - **Gap:** No fresh EP19 run/report in this programme; no explicit "Day 19 is
    done" evidence tying behaviour to acceptance criteria.

- **Day 20 – RAG Session Closure**
  - **Expectation:** RAG vs non-RAG comparison with conclusions.
  - **Reality:** RAG use case and demos implemented, Epic 20 spec exists, but
    progress tracker shows EP20 as Planned.
  - **Gap:** No updated EP20 report in the current cycle summarising RAG impact
    vs baseline and marking challenge closure.

- **Day 21 – Reranking Impact Report**
  - **Expectation:** Second-stage reranking / filtering with measurable quality
    improvements.
  - **Reality:** Reranker configuration, metrics and demos exist; EP21 still in
    planned stages.
  - **Gap:** No consolidated evaluation (before/after rerank) recorded as part
    of the current programme to close Day 21 requirements.

- **Day 22 – Enforced Citations**
  - **Expectation:** All RAG answers contain citations; hallucinations reduced.
  - **Reality:** Citation patterns documented for Analyst and example sessions;
    code can surface citations.
  - **Gap:** No specific RAG endpoint or flow where citations are *mandatory*
    and enforced by tests as part of the Day 22 closure.


