# API Documentation

## Overview

The AI Challenge API provides REST endpoints for code generation, review, and
observability. When `USE_MODULAR_REVIEWER=1` the review pipeline is powered by
`packages/multipass-reviewer` and executes against the shared Mongo/LLM
infrastructure.

**Base URL**: `http://localhost:8000` (or the ingress configured in
`docker-compose.butler.yml`)

**Interactive Docs**: `http://localhost:8000/docs`

## Authentication

No authentication is required for local development. Downstream deployments can
add FastAPI dependencies or ingress rules.

## Rate Limiting

No rate limits are enforced in local or staging environments.

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created (review task)
- `202 Accepted`: Asynchronous task accepted (not currently used)
- `400 Bad Request`: Invalid request parameters or validation failure
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: Uploaded archive exceeded size limit
- `500 Internal Server Error`: Unhandled exception
- `503 Service Unavailable`: Downstream service unavailable

## Agents

### Generate Code

**POST** `/api/agents/generate`

Generate code from a natural language prompt.

Request body:

```json
{
  "prompt": "Create a REST API for task management",
  "agent_name": "generator",
  "model_name": "starcoder",
  "max_tokens": 1200,
  "temperature": 0.6
}
```

Response:

```json
{
  "task_id": "gen_123",
  "status": "completed",
  "result": "def handler(...): ...",
  "token_info": {
    "input_tokens": 120,
    "output_tokens": 280,
    "total_tokens": 400
  }
}
```

### Review Code (inline)

**POST** `/api/agents/review`

Review a code snippet with the selected model. Use when archives are not
required. Response mirrors `generate` with review content.

## Review Pipeline

All archive-based reviews use the `/api/v1/reviews` namespace.

### Create Review Task

**POST** `/api/v1/reviews`

Content type: `multipart/form-data`

Form fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `student_id` | string | yes | Author identifier |
| `assignment_id` | string | yes | Assignment slug |
| `new_commit` | string | yes | Commit SHA for new submission |
| `old_commit` | string | no | Previous commit SHA |
| `new_zip` | file | yes | ZIP archive of current submission |
| `old_zip` | file | no | ZIP archive of previous submission |
| `logs_zip` | file | no | Optional logs for pass 4 analysis |

Example `curl`:

```bash
curl -X POST http://localhost:8000/api/v1/reviews \
  -F student_id=student-1 \
  -F assignment_id=HW_MODULAR \
  -F new_commit=abc123 \
  -F new_zip=@new_submission.zip \
  -F logs_zip=@logs.zip
```

Response (`201 Created`):

```json
{
  "task_id": "rev_c0ffee",
  "status": "pending",
  "student_id": "student-1",
  "assignment_id": "HW_MODULAR",
  "created_at": "2025-11-07T18:55:31.123456"
}
```

Tasks are processed asynchronously by the unified task worker. When the modular
reviewer flag is enabled the worker delegates to `ModularReviewService`, which
uses the shared LLM and shared MongoDB.

### Get Review Status

**GET** `/api/v1/reviews/{task_id}`

Returns the current status and, when completed, the review report summary.

Response example:

```json
{
  "task_id": "rev_c0ffee",
  "status": "completed",
  "student_id": "student-1",
  "assignment_id": "HW_MODULAR",
  "created_at": "2025-11-07T18:55:31.123456",
  "completed_at": "2025-11-07T18:57:02.654321",
  "result": {
    "session_id": "session_student-1",
    "total_findings": 5,
    "haiku": "Code flows like rivers..."
  }
}
```

If the task ID is unknown the API returns `404`.

## Health & Metrics

### Healthcheck

**GET** `/health`

Aggregates MongoDB connectivity, LLM reachability, and background worker health.

### Metrics

**GET** `/metrics`

Prometheus-formatted metrics, including modular reviewer counters/histograms
when the feature flag is active:

- `review_checker_findings_total{checker_name="python_style",severity="major"}`
- `review_checker_runtime_seconds_bucket{checker_name="component",le="0.5"}`

## Deployment Notes

- The API expects the shared networks to be present; see
  `docs/guides/en/DEVELOPMENT.md` for docker commands.
- Archive uploads are written to `review_archives/` within the API container.
  Ensure persistent storage if running outside development.
- Large reviews can be tuned via `archive_max_total_size_mb` in settings.

## Versioning & Changelog

Refer to the repository `CHANGELOG.md` and `packages/multipass-reviewer/CHANGELOG.md`
for endpoint or behaviour updates tied to releases.
