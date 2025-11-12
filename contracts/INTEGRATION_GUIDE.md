# Code Review API Integration Guide

## Overview

This guide explains how to integrate with the Code Review API for automated code review of student submissions. The API supports multipart file uploads and asynchronous task processing.

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Request Format](#request-format)
4. [Response Format](#response-format)
5. [Error Handling](#error-handling)
6. [Archive Formats](#archive-formats)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

## Quick Start

### 1. Submit a Review

```bash
curl -X POST "http://localhost:8000/api/v1/reviews" \
  -F "student_id=student_123" \
  -F "assignment_id=HW2" \
  -F "new_commit=abc123def456" \
  -F "new_zip=@new_submission.zip"
```

### 2. Check Status

```bash
curl -X GET "http://localhost:8000/api/v1/reviews/task_abc123"
```

### 3. Wait for Completion

Poll the status endpoint until `status` is `"completed"` or `"failed"`.

## API Endpoints

### POST /api/v1/reviews

Creates a new code review task.

**Request**: `multipart/form-data`

**Required Fields**:
- `student_id` (string): Student identifier
- `assignment_id` (string): Assignment identifier
- `new_commit` (string): Commit hash for new submission (non-empty)
- `new_zip` (file): ZIP archive with new submission code

**Optional Fields**:
- `old_zip` (file): ZIP archive with previous submission code
- `logs_zip` (file): ZIP archive with runtime logs (see [Log Archive Format](./log_archive_format.md))
- `old_commit` (string): Commit hash for previous submission

**Response**: `201 Created`

```json
{
  "task_id": "task_abc123",
  "status": "queued",
  "student_id": "student_123",
  "assignment_id": "HW2",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### GET /api/v1/reviews/{task_id}

Retrieves the status of a review task.

**Response**: `200 OK`

```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "student_id": "student_123",
  "assignment_id": "HW2",
  "created_at": "2025-01-15T10:30:00Z",
  "finished_at": "2025-01-15T10:35:00Z",
  "result": {
    "session_id": "session_xyz789",
    "overall_score": 75
  }
}
```

**Status Values**:
- `queued`: Task is waiting to be processed
- `running`: Task is currently being processed
- `completed`: Task completed successfully
- `failed`: Task failed with an error

## Request Format

### Multipart Form Data

The API uses `multipart/form-data` for file uploads. All fields are sent as form fields, with files as binary attachments.

### File Size Limits

- **Default**: 100 MB per archive (configurable via `ARCHIVE_MAX_TOTAL_SIZE_MB`)
- **Error**: `413 Request Entity Too Large` if exceeded

### Supported Archive Formats

- **Code archives**: ZIP files containing Python code, notebooks, config files
- **Log archives**: ZIP files with `logs/` directory (see [Log Archive Format](./log_archive_format.md))

## Response Format

### Success Response

All successful responses return JSON with the following structure:

```json
{
  "task_id": "string",
  "status": "queued|running|completed|failed",
  "student_id": "string",
  "assignment_id": "string",
  "created_at": "ISO 8601 datetime",
  "finished_at": "ISO 8601 datetime (optional)",
  "result": { ... } (optional, when completed),
  "error": "string" (optional, when failed)
}
```

### Result Payload (completed tasks)

```json
{
  "session_id": "session_xyz789",
  "overall_score": 88,
  "report": {
    "markdown": "# Review\n...",
    "static_analysis_results": [
      {
        "tool": "flake8",
        "summary": "2 warnings",
        "entries": ["app/main.py:12 E501 line too long", "utils/helpers.py:45 W292 no newline"]
      }
    ],
    "pass_4_logs": {
      "status": "completed",
      "results": [
        {
          "component": "docker",
          "classification": "ERROR",
          "description": "Container exited with status 1",
          "root_cause": "Missing ENV VAR FOO",
          "recommendations": "Add FOO=... to compose file",
          "confidence": 0.82,
          "count": 3
        }
      ]
    },
    "haiku": "Code finds its balance\nLogs whisper the hidden cause\nFix blooms in review"
  },
  "published_via": "mcp"  // or "fallback"
}
```

### Error Response

```json
{
  "detail": "Error message"
}
```

**HTTP Status Codes**:
- `400 Bad Request`: Validation error
- `404 Not Found`: Task not found
- `413 Request Entity Too Large`: Archive exceeds size limit
- `500 Internal Server Error`: Server error

## Error Handling

### Retry Logic

For transient errors (5xx), implement exponential backoff:

```python
import time
import requests

def submit_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.submit_review(...)
        except requests.HTTPError as e:
            if e.response.status_code >= 500 and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue
            raise
```

### Timeout Handling

- **Request timeout**: 60 seconds for POST, 30 seconds for GET
- **Task processing**: Typically 2-5 minutes (depends on code size and complexity)

## Archive Formats

### Code Archive Format

ZIP file containing:
- Python files (`.py`)
- Jupyter notebooks (`.ipynb`)
- Configuration files (`.yml`, `.yaml`, `.json`)
- Documentation (`.md`, `.txt`)

**Structure**: Flat or nested directories (both supported)

**Example**:
```
submission.zip
├── main.py
├── utils.py
├── config/
│   └── settings.yaml
└── README.md
```

### Log Archive Format

See [Log Archive Format Specification](./log_archive_format.md) for details.

**Key Points**:
- Must contain `logs/` directory
- Supported formats: `checker.log`, `run_stdout.txt`, `run_stderr.txt`, `container-*.log`
- Maximum 100 MB total size

## Best Practices

### 1. Include Commit Hashes

`new_commit` is mandatory and must match the uploaded archive. Provide `old_commit` when available. This enables:
- Better diff analysis
- Tracking submission history
- Integration with version control systems

### 2. Provide Previous Submission

Include `old_zip` when available. This enables:
- Comparative analysis
- Change detection
- Progress tracking

### 3. Include Logs

Include `logs_zip` for runtime analysis. This enables:
- Pass 4 (Runtime Analysis)
- Bug detection from logs
- Performance issue identification

### 4. Consume Enriched Results

- Parse `result.report.static_analysis_results` to surface lint/type errors to students.
- Use `result.report.pass_4_logs.results` to highlight runtime failures and remediation tips.
- Display the `haiku` alongside the summary to provide qualitative feedback.
- Track `published_via` (`mcp` vs `fallback`) for operational monitoring.

### 5. Polling Strategy

- **Initial delay**: Wait 10 seconds before first poll
- **Poll interval**: 5-10 seconds
- **Max wait**: 5-10 minutes (adjust based on typical processing time)

### 6. Error Recovery

- **Task failed**: Log error, notify user, allow resubmission
- **Timeout**: Check if task is still running, extend timeout if needed
- **Network errors**: Retry with exponential backoff

## MCP Publishing

1. The reviewer LLM discovers the `submit_review_result` tool via `MCPHTTPClient` (`HW_CHECKER_MCP_URL`).
2. `_prepare_mcp_publish_context` instructs the LLM to supply `student_id`, `submission_hash`, `review_content`, `session_id`, `overall_score`.
3. The tool is executed; on success the review is stored by HW Checker infrastructure.
4. If the MCP call fails or `HW_CHECKER_MCP_ENABLED=false`, the system falls back to `ExternalAPIClient` using the same payload.
5. Downstream integrations should monitor the `published_via` field (`mcp` vs `fallback`).

Set the following environment variables for production deployments:

- `HW_CHECKER_MCP_URL` (default `http://mcp-server:8005`)
- `HW_CHECKER_MCP_ENABLED=true`
- Optional fallback: `EXTERNAL_API_URL`, `EXTERNAL_API_KEY`, `EXTERNAL_API_TIMEOUT`

## Examples

### Python Example

See [python_example.py](./examples/python_example.py) for a complete Python client implementation.

### cURL Example

See [curl_example.sh](./examples/curl_example.sh) for cURL command examples.

### Minimal Example

```python
import requests

# Submit review
files = {"new_zip": open("submission.zip", "rb")}
data = {
    "student_id": "student_123",
    "assignment_id": "HW2",
}
response = requests.post(
    "http://localhost:8000/api/v1/reviews",
    files=files,
    data=data,
)
task = response.json()
print(f"Task ID: {task['task_id']}")

# Check status
task_id = task["task_id"]
status_response = requests.get(
    f"http://localhost:8000/api/v1/reviews/{task_id}"
)
status = status_response.json()
print(f"Status: {status['status']}")
```

## External API Integration

When a review completes, the system publishes results to an external API (if configured).

### Payload Schema

See [hw_check_payload_schema.json](./hw_check_payload_schema.json) for the JSON schema.

### Webhook Setup

To receive review completion notifications:

1. Configure `EXTERNAL_API_URL` and `EXTERNAL_API_KEY` in environment
2. Implement endpoint at `POST {EXTERNAL_API_URL}/reviews`
3. Handle payload according to schema

### Example Payload

```json
{
  "task_id": "task_abc123",
  "student_id": "student_123",
  "assignment_id": "HW2",
  "session_id": "session_xyz789",
  "overall_score": 75,
  "new_commit": "abc123def456"
}
```

## OpenAPI Specification

For complete API documentation, see [review_api_v1.yaml](./review_api_v1.yaml).

You can use tools like Swagger UI or Postman to import the OpenAPI spec:

```bash
# View in Swagger UI
docker run -p 8080:8080 -e SWAGGER_JSON=/api/review_api_v1.yaml \
  -v $(pwd)/contracts:/api swaggerapi/swagger-ui
```

## Support

For questions or issues:
1. Check this guide and examples
2. Review OpenAPI specification
3. Contact support team
