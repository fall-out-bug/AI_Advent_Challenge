# Modular Reviewer API (EN)

## 1. Scope

The modular reviewer is the canonical implementation for code-review automation.
It can be invoked from:

- Application layer (`ModularReviewService.review_submission`)
- MCP homework-review tool
- Background workers (Unified Task Worker)
- Manual scripts or CLI utilities

This document describes the primary integration surface, input/output contracts,
and observability hooks.

## 2. Application Service Contract

Location: `src/application/services/modular_review_service.py`

### Signature

```python
await ModularReviewService.review_submission(
    new_archive: SubmissionArchive,
    previous_archive: SubmissionArchive | None,
    assignment_id: str,
    student_id: str,
) -> MultiPassReport
```

### Inputs

- `new_archive`: extracted code files (`SubmissionArchive.code_files`)
- `previous_archive`: optional archive for diffing
- `assignment_id`: logical assignment identifier
- `student_id`: unique student identifier

The service internally:

1. Adapts archive reader / LLM client to package interfaces.
2. Builds `ReviewConfig` using `ReviewConfigBuilder`.
3. Executes `MultiPassReviewerAgent.review_from_archives`.
4. Converts the package report to legacy `MultiPassReport`.
5. Persists output via `HomeworkReviewRepository` and emits metrics.

### Outputs (`MultiPassReport`)

Located in `src/domain/models/code_review_models.py`.

```python
@dataclass(slots=True)
class MultiPassReport:
    assignment_id: str | None
    student_id: str | None
    passes: list[PassFindings]
    summary: str
    errors: list[dict[str, Any]]
    created_at: datetime
```

Each `PassFindings` entry contains:

- `name`: pass name (`architecture`, `components`, `synthesis`)
- `status`: `"completed"` or `"failed"`
- `summary`: text summary (RU localisation by default)
- `findings`: list of structured findings
- `error`: optional error message

### Error Handling

- Partial failures return `status="failed"` on the specific pass while the
  overall review succeeds.
- Global failures raise `ReviewSubmissionError` and mark the task as failed.
- All errors include `trace_id` for correlation in logs/metrics.

## 3. MCP Homework Review Tool

Location: `src/presentation/mcp/tools/homework_review_tool.py`

### Tool Name

`review_homework_archive`

### Parameters

| Field | Type | Description |
|-------|------|-------------|
| `archive_path` | `str` | Path to uploaded ZIP archive |
| `assignment_id` | `str` | Assignment identifier |
| `student_id` | `str` | Student identifier |
| `language` | `str` | Programming language (default: `"python"`) |
| `previous_archive_path` | `str` | Optional previous submission |

### Response

```json
{
  "status": "success",
  "report": {
    "summary": "...",
    "passes": [
      {
        "name": "architecture",
        "status": "completed",
        "summary": "...",
        "findings": [
          {"severity": "warning", "title": "...", "details": "..."}
        ]
      }
    ],
    "errors": []
  }
}
```

Failures return:

```json
{
  "status": "error",
  "error": "Reason for failure"
}
```

### Behaviour

- Uses `ZipArchiveService` for extraction (path validation, anti zip-bomb).
- Invokes `ModularReviewService` with real settings.
- Emits structured logs with `trace_id`.
- Propagates pass-level status/errors back to MCP clients.

## 4. Observability

### Metrics

`multipass_reviewer.infrastructure.monitoring.metrics` exposes:

- `multipass_checker_findings_total{checker,severity}`
- `multipass_checker_runtime_seconds{checker}`
- `multipass_pass_runtime_seconds{pass_name}`
- `multipass_llm_tokens_total{model,direction}`
- `multipass_llm_latency_seconds{model}`

Application-level wrapper (`src/infrastructure/monitoring/checker_metrics.py`)
records aggregate pass observations.

### Logging

`ReviewLogger` attaches:

- `trace_id`
- pass status, runtime, findings count
- LLM requests/responses metadata

Retrieve logs via `ReviewLogger.get_all_logs()` for debugging or publishing.

## 5. Feature Flags & Configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| `USE_MODULAR_REVIEWER` | `True` | Toggle between modular vs legacy implementation |
| `review_rate_limit_*` | See `settings.py` | Per-student and per-assignment rate control |
| `llm_model`, `llm_timeout` | Settings defaults | Model alias and HTTP timeout |
| `allowed_archive_globs` | Settings list | Whitelisted file patterns during extraction |

Configuration lives in `src/infrastructure/config/settings.py` and is managed by
Pydantic Settings (env-first strategy).

## 6. Example Usage (Script)

```python
from src.application.services.modular_review_service import ModularReviewService
from src.infrastructure.archive.archive_service import ZipArchiveService
from src.infrastructure.diff.diff_analyzer import DiffAnalyzer
from shared.shared_package.clients.unified_client import UnifiedModelClient
from src.infrastructure.logging.review_logger import ReviewLogger

archive_service = ZipArchiveService()
diff_analyzer = DiffAnalyzer()
llm_client = UnifiedModelClient(timeout=120.0)
review_logger = ReviewLogger()

service = ModularReviewService(
    archive_service=archive_service,
    diff_analyzer=diff_analyzer,
    llm_client=llm_client,
    review_logger=review_logger,
)

report = await service.review_submission(
    new_archive="/tmp/submissions/new.zip",
    previous_archive=None,
    assignment_id="HW2",
    student_id="student123",
)

print(report.summary)
```

## 7. Next Steps

- Use the CLI backoffice (WIP) for manual trigger/testing.
- Refer to `docs/guides/en/USER_GUIDE.md` for benchmark results and troubleshooting.
- See `docs/reference/ru/API_REVIEWER.ru.md` for Russian localisation of this document.
