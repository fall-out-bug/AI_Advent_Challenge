# Day 17 – Code Review Platform Upgrades

## Overview

Day 17 evolves the homework review platform from a 3-pass prototype into a production-ready pipeline with static analysis, log diagnostics, and automated publishing to the external HW Checker MCP server.

## Key Improvements

- **Static Analysis Stage**: Flake8, Pylint, MyPy, Black, and isort run after Pass 3. Findings are normalized and injected into `MultiPassReport.static_analysis_results`.
- **Pass 4 Log Analysis**: Runtime logs (checker, Docker stdout/stderr, compose) are parsed, normalized, and summarised by `LLMLogAnalyzer` with root-cause and remediation tips.
- **MCP-first Publishing**: The reviewer LLM calls the external `submit_review_result` tool via `MCPHTTPClient`; failures fall back to `ExternalAPIClient`.
- **Haiku Postscript**: Every report ends with an auto-generated haiku; a deterministic fallback is used on LLM errors.
- **Integration Contracts**: Updated OpenAPI spec, JSON schema, and CLI examples describing the enriched payload and mandatory `new_commit` field.

## Architecture Changes

```
Archive → Diff Analyzer
            ↓
       Pass 1 (Architecture)
            ↓
       Pass 2 (Components)
            ↓
       Pass 3 (Synthesis)
            ↓
   Static Analysis (lint & format)
            ↓
       Pass 4 (Log Analysis)
            ↓
 Report + Haiku → MCP Publishing (tool call → HTTP fallback)
```

Key components:

- **Static Analysis**: `CodeQualityChecker`, per-tool runners, aggregation utilities.
- **Log Pipeline**: `LogParserImpl`, `LogNormalizer`, `LLMLogAnalyzer` with severity limits from `Settings`.
- **Publishing**: `MCPHTTPClient` for tool discovery/execution, `ExternalAPIClient` for fallback.
- **Settings**: `hw_checker_mcp_url`, `hw_checker_mcp_enabled`, `log_analysis_*` caps and timeouts.

## Worker Wiring

`SummaryWorker` now instantiates:

- `MCPHTTPClient(base_url=settings.hw_checker_mcp_url)` when MCP publishing is enabled.
- `ExternalAPIClient` as fallback (optional if legacy API disabled).
- Log analysis stack (`LogParserImpl`, `LogNormalizer`, `LLMLogAnalyzer`).

Queue handling remains the same: `pick_next_queued(TaskType.CODE_REVIEW)` → `ReviewSubmissionUseCase.execute()`.

## Publishing Flow

1. Discover MCP tools (`MCPHTTPClient.discover_tools`).
2. Prompt LLM to produce tool arguments using `_prepare_mcp_publish_context`.
3. Parse LLM JSON (`_parse_tool_call_response`) and enrich missing fields.
4. Call `submit_review_result` via MCP; log success.
5. If MCP call fails or MCP disabled, call `ExternalAPIClient.publish_review`.

## Testing

- `tests/unit/application/use_cases/test_review_submission_pass4.py` – validates log-analysis execution.
- `tests/unit/application/use_cases/test_review_submission_llm_mcp.py` – covers tool invocation, JSON parsing, and fallback logic.
- Contract tests under `tests/contracts/` check new payload requirements.

## Migration Notes

- Legacy docker-compose manifests moved to `archive/docker-compose/`; use `make butler-up` (production) or `make butler-down` for teardown.
- Ensure the following env vars are present:
  - `HW_CHECKER_MCP_URL` (default `http://mcp-server:8005`)
  - `HW_CHECKER_MCP_ENABLED` (default `true`)
  - `EXTERNAL_API_*` (optional fallback)
- Review API clients must provide `new_commit` in both REST and MCP payloads.

See `docs/day17/INTEGRATION_CONTRACTS.md` for contract details and payload examples.

