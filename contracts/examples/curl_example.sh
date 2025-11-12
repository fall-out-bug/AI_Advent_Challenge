#!/bin/bash
# Example: Submit code review using cURL

# Configuration
API_URL="http://localhost:8000"
STUDENT_ID="student_123"
ASSIGNMENT_ID="HW2"
NEW_COMMIT="abc123def456"
OLD_COMMIT="xyz789uvw012"

# File paths (adjust to your actual files)
NEW_ZIP="./new_submission.zip"
OLD_ZIP="./old_submission.zip"
LOGS_ZIP="./logs.zip"

# Submit review with all files
curl -X POST "${API_URL}/api/v1/reviews" \
  -F "student_id=${STUDENT_ID}" \
  -F "assignment_id=${ASSIGNMENT_ID}" \
  -F "new_commit=${NEW_COMMIT}" \
  -F "old_commit=${OLD_COMMIT}" \
  -F "new_zip=@${NEW_ZIP}" \
  -F "old_zip=@${OLD_ZIP}" \
  -F "logs_zip=@${LOGS_ZIP}"

# Example response:
# {
#   "task_id": "task_abc123",
#   "status": "queued",
#   "student_id": "student_123",
#   "assignment_id": "HW2",
#   "created_at": "2025-01-15T10:30:00Z"
# }

# Submit review with only new submission (minimal)
curl -X POST "${API_URL}/api/v1/reviews" \
  -F "student_id=${STUDENT_ID}" \
  -F "assignment_id=${ASSIGNMENT_ID}" \
  -F "new_commit=${NEW_COMMIT}" \
  -F "new_zip=@${NEW_ZIP}"

# Check review status
TASK_ID="task_abc123"
curl -X GET "${API_URL}/api/v1/reviews/${TASK_ID}"

# Example response (completed):
# {
#   "task_id": "task_abc123",
#   "status": "completed",
#   "student_id": "student_123",
#   "assignment_id": "HW2",
#   "created_at": "2025-01-15T10:30:00Z",
#   "finished_at": "2025-01-15T10:35:00Z",
#   "result": {
#     "session_id": "session_xyz789",
#     "overall_score": 75
#   }
# }
