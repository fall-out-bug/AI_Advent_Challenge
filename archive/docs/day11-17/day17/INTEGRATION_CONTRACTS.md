# Day 17 Integration Contracts

## Overview

The review publishing pipeline now exposes a richer contract for downstream systems (HW Checker MCP, legacy HTTP API). This document summarises the artefacts, required fields, and example payloads.

## Artefacts

- **OpenAPI**: `contracts/review_api_v1.yaml`
- **JSON Schema**: `contracts/hw_check_payload_schema.json`
- **Examples**: `contracts/examples/curl_example.sh`, `contracts/examples/python_example.py`
- **Tests**: `tests/contracts/test_api_spec.py`, `tests/contracts/test_payload_schema.py`

## Required Fields (MCP & REST)

| Field | Type | Description |
|-------|------|-------------|
| `student_id` | string | Student identifier (textual, e.g. “Ivanov Ivan”) |
| `assignment_id` | string | Homework identifier |
| `new_commit` | string | Commit hash for the new submission (minLength=1) |
| `session_id` | string | Review session id returned by `ReviewSubmissionUseCase` |
| `overall_score` | number | Summary score (0-100 heuristic) |
| `review_content` | string | Markdown report including static analysis, Pass 4 logs, haiku |

Optional fields:

- `old_commit` – previous commit hash (if available)
- `logs_zip_path` – stored path for diagnostic logs
- `static_analysis_results` – structured lint/type data
- `pass_4_logs` – log-analysis metadata (component, classification, recommendations)

## MCP Tool Invocation

```json
{
  "tool": "submit_review_result",
  "arguments": {
    "student_id": "Ivanov Ivan",
    "submission_hash": "commit123",
    "review_content": "# Review\n...",
    "session_id": "session-42",
    "overall_score": 88
  }
}
```

Client code:

```python
from src.presentation.mcp.http_client import MCPHTTPClient

mcp = MCPHTTPClient(base_url=settings.hw_checker_mcp_url)
tool_args = {...}
await mcp.call_tool("submit_review_result", tool_args)
```

## HTTP Fallback Payload

```json
{
  "task_id": "task-commit123",
  "student_id": "student_123",
  "assignment_id": "HW2",
  "session_id": "session-42",
  "overall_score": 88,
  "new_commit": "commit123",
  "review_url": "https://drive.google.com/...",
  "static_analysis_results": [...],
  "pass_4_logs": {
    "status": "completed",
    "results": [
      {
        "component": "docker",
        "classification": "ERROR",
        "description": "...",
        "root_cause": "missing env",
        "recommendations": "export FOO",
        "confidence": 0.74,
        "count": 3
      }
    ]
  }
}
```

## Validation & Testing

- `pytest tests/contracts/test_api_spec.py` – ensures OpenAPI schema marks `new_commit` as required/non-null, documents new sections.
- `pytest tests/contracts/test_payload_schema.py` – validates JSON schema for MCP/REST payloads, including missing-field failures.
- Unit tests for publishing: `test_review_submission_llm_mcp.py` and `test_review_submission_pass4.py`.

## Integration Checklist

1. Configure environment variables:
   - `HW_CHECKER_MCP_URL` (default `http://mcp-server:8005`)
   - `HW_CHECKER_MCP_ENABLED=true`
   - Optional fallback: `EXTERNAL_API_URL`, `EXTERNAL_API_KEY`
2. Ensure worker has access to review archives and log zips.
3. Provide `new_commit` in every `/api/v1/reviews` request or MCP tool call.
4. Consume `pass_4_logs` and `static_analysis_results` in downstream systems as structured data.

For a detailed architectural narrative, see `docs/day17/README.md` and `docs/review_system_architecture.md`.

