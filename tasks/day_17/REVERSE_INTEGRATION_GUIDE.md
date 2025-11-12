# Reverse Integration Guide: Submitting Review Results

## Overview
This document explains how an external review service can submit completed code review results back to the HW Checker MCP API. The current flow assumes the external reviewer runs inside the same Docker infrastructure and has network access to the `hw-checker-infra` environment.

## Network & Access Requirements
- **Endpoint hostname**: `mcp-server` (from within `ai-challenge-network`)
- **Endpoint URL**: `http://mcp-server:8005/api/review/submit_result`
- **HTTP method**: `POST`
- **Authentication**: Not required (feature is gated by network access); future iterations will add auth tokens.
- **Content type**: `application/json`

> **Note:** If your service defines its own hostname alias, point it to the MCP container’s IP on `ai-challenge-network`.

## Request Schema
```json
{
  "student_id": "Surname Name",
  "submission_hash": "0123456789abcdef...",
  "review_content": "# Markdown review...",
  "session_id": "optional external session id",
  "overall_score": 85
}
```

| Field            | Type    | Required | Description                                                     |
|------------------|---------|----------|-----------------------------------------------------------------|
| `student_id`     | string  | ✅       | Student identifier in `"Surname Name"` format                   |
| `submission_hash`| string  | ✅       | Git commit hash associated with the submission                  |
| `review_content` | string  | ✅       | Markdown document containing the review                         |
| `session_id`     | string  | ❌       | Optional identifier used by the external review system          |
| `overall_score`  | number  | ❌       | Optional numeric score (0-100, or any reviewer-specific scale)  |

## Response Schema
```json
{
  "status": "ok",
  "message": "Review processed successfully"
}
```

| Field      | Description                                                                     |
|------------|---------------------------------------------------------------------------------|
| `status`   | `"ok"` if processing succeeded, `"error"` when issues were encountered          |
| `message`  | Human-readable summary (contains concatenated warnings when `status = "error"`) |

> The endpoint always returns HTTP 200. Errors are reported in the payload and logged server-side.

## Processing Steps on MCP Side
1. Uploads the markdown content to Google Drive (if `HW_GDRIVE_FOLDER_ID` is configured).
2. Updates the corresponding `CheckJob.review_link` in PostgreSQL.
3. Adds/updates the `"review"` column in Google Sheets with the new link.
4. Stores optional `session_id` and `overall_score` inside job metadata for auditing.
5. Logs all errors but does not raise exceptions (idempotent behaviour).

## Example: curl
```bash
curl -X POST "http://mcp-server:8005/api/review/submit_result" \
  -H "Content-Type: application/json" \
  -d '{
        "student_id": "Селифанов Владимир",
        "submission_hash": "cafe1234deadbeef5678",
        "review_content": "# Review\n\n## Summary\nВсе отлично!",
        "session_id": "review-task-42",
        "overall_score": 92
      }'
```

## Example: Python
```python
import requests

payload = {
    "student_id": "Ivanov Ivan",
    "submission_hash": "0123456789abcdef",
    "review_content": "# Review\n\n## Summary\nLooks good.",
    "session_id": "ext-review-001",
    "overall_score": 75,
}

response = requests.post(
    "http://mcp-server:8005/api/review/submit_result",
    json=payload,
    timeout=30,
)
response.raise_for_status()
print(response.json())
```

## Field Mapping vs Internal System
| External Field     | Internal Destination                                      |
|--------------------|-----------------------------------------------------------|
| `student_id`       | Matching `CheckJob.student_id` and Google Sheet “name”    |
| `submission_hash`  | `CheckJob.commit_hash` (locates the job)                  |
| `review_content`   | Uploaded to Google Drive (`review_link` stored)           |
| `session_id`       | Stored in `CheckJob.job_metadata["review_session_id"]`    |
| `overall_score`    | Stored in `CheckJob.job_metadata["review_overall_score"]` |

## Error Handling
- **Google Drive unavailable**: Review is still logged in DB and Sheets; message contains warning.
- **Job not found**: Response `status="error"` with message `"No job found..."`.
- **Sheets update fails**: Warning appended to `message`, logs include full stack trace.

All steps are idempotent—re-sending the same payload is safe and overwrites the previous review link.

## Verification Checklist
After integrating, verify:
1. Endpoint reachable from your container (`curl` example above).
2. Review markdown appears in configured Google Drive folder.
3. PostgreSQL `check_jobs` table has `review_link` populated for the job.
4. Google Sheet gains/updates the “review” column with the generated link.
5. MCP logs (`checker.log`) show `"Received review result"` entry.

## Support
Questions or issues? Contact the HW Checker maintainers or open a task in the project tracker with details (payload, timestamp, logs).
