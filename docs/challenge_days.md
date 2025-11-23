# 28-Day Journey

This page condenses the entire AI Challenge into one glance. Each day built on the
previous one, culminating in Alfred—the God Agent that now fronts the product via Telegram.

| Day | Theme | Outcome |
|-----|-------|---------|
| 1 | HTTP chat bootstrap | First end-to-end LLM chat over HTTP. |
| 2 | JSON responses | Strict schema-enforced outputs → DTO layer. |
| 3 | Advisor mode | Multi-turn advisor with session state patterns. |
| 4 | Temperature control | Deterministic vs creative sampling modes. |
| 5 | Local models | Dockerised local LLM stack. |
| 6 | Testing framework | Pytest pipeline, fixtures, quality reports. |
| 7 | Multi-agent orchestration | First coordinator for specialised agents. |
| 8 | Token economics | Context compression + budgeting strategy. |
| 9 | MCP integration | Initial MCP server & tool catalogue. |
| 10 | Production MCP | Streaming, caching, orchestration hardening. |
| 11 | Butler bot FSM | 24/7 Telegram butler with scheduled digests. |
| 12 | PDF digests | Automated PDF pipeline plugged into Butler. |
| 13 | Butler refactor | Clean Architecture + phased use cases. |
| 14 | Multi-pass reviewer | Homework/code review with antagonistic agents. |
| 15 | LLM-as-judge | Quality governance & fine-tuning guardrails. |
| 16 | External memory | Persistent Mongo-backed profile/memory. |
| 17 | Code-review platform | MCP publishing + static analysis contracts. |
| 18 | Foundation recap | Consolidated epics 00–06 for reuse. |
| 19 | Embedding index | Ingest → chunk → embed → store pipeline. |
| 20 | RAG vs non-RAG | Side-by-side answering agent comparisons. |
| 21 | RAG++ refactor | Repo cleanup + reranker-ready architecture. |
| 22 | RAG citations | Mandatory source attribution with tests. |
| 23 | Observability | Metrics/logs/traces/benchmarks across stack. |
| 24 | Voice control | Whisper-powered voice → command path. |
| 25 | Personalised Butler | Alfred persona: profile + memory-first replies. |
| 26 | Test Agent | Autonomous code/test generation & execution. |
| 27 | Reliability hardening | Large-module regression + rollback drills. |
| 28 | God Agent Alfred | Unified intent router, planner, and skill graph exposed via Telegram. |

All supporting specs live under `docs/specs/`, with Epic 28 capturing the final architecture.
Historic guides live in `docs/reference/legacy/library/` for future archaeology. This file is the canonical high-level summary.
