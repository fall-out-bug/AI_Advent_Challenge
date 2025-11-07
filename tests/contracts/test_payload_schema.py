"""Contract tests for payload schema compliance.

Following TDD principles: tests validate that payloads sent to external API
match the JSON schema specification.
"""

import json
from pathlib import Path

import pytest
import jsonschema
from jsonschema import validate, ValidationError


@pytest.fixture
def payload_schema() -> dict:
    """Load payload JSON schema."""
    schema_path = (
        Path(__file__).parent.parent.parent
        / "contracts"
        / "hw_check_payload_schema.json"
    )
    with open(schema_path) as f:
        return json.load(f)


class TestPayloadSchemaCompliance:
    """Test payload compliance with JSON schema."""

    def test_valid_minimal_payload(self, payload_schema: dict):
        """Test that minimal required payload is valid."""
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            "assignment_id": "HW2",
            "session_id": "session_xyz789",
            "overall_score": 75,
            "new_commit": "abc123def456",
        }
        validate(instance=payload, schema=payload_schema)

    def test_valid_full_payload(self, payload_schema: dict):
        """Test that full payload with optional fields is valid."""
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            "assignment_id": "HW2",
            "session_id": "session_xyz789",
            "overall_score": 75,
            "new_commit": "abc123def456",
        }
        validate(instance=payload, schema=payload_schema)

    def test_missing_required_field(self, payload_schema: dict):
        """Test that missing required field raises ValidationError."""
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            # Missing assignment_id
            "session_id": "session_xyz789",
            "overall_score": 75,
            "new_commit": "abc123def456",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=payload, schema=payload_schema)
        assert "assignment_id" in str(exc_info.value)

    def test_missing_new_commit(self, payload_schema: dict) -> None:
        """Test that missing new_commit raises ValidationError."""
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            "assignment_id": "HW2",
            "session_id": "session_xyz789",
            "overall_score": 75,
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=payload, schema=payload_schema)
        assert "new_commit" in str(exc_info.value)

    def test_invalid_overall_score_type(self, payload_schema: dict):
        """Test that invalid overall_score type raises ValidationError."""
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            "assignment_id": "HW2",
            "session_id": "session_xyz789",
            "overall_score": "75",  # String instead of integer
            "new_commit": "abc123def456",
        }
        with pytest.raises(ValidationError):
            validate(instance=payload, schema=payload_schema)

    def test_overall_score_out_of_range(self, payload_schema: dict):
        """Test that overall_score out of range raises ValidationError."""
        # Test below minimum
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            "assignment_id": "HW2",
            "session_id": "session_xyz789",
            "overall_score": -1,
            "new_commit": "abc123def456",
        }
        with pytest.raises(ValidationError):
            validate(instance=payload, schema=payload_schema)

        # Test above maximum
        payload["overall_score"] = 101
        with pytest.raises(ValidationError):
            validate(instance=payload, schema=payload_schema)

    def test_additional_properties_not_allowed(self, payload_schema: dict):
        """Test that additional properties are not allowed."""
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            "assignment_id": "HW2",
            "session_id": "session_xyz789",
            "overall_score": 75,
            "extra_field": "not_allowed",
            "new_commit": "abc123def456",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=payload, schema=payload_schema)
        assert "extra_field" in str(exc_info.value)

    def test_string_field_types(self, payload_schema: dict):
        """Test that all string fields accept strings."""
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            "assignment_id": "HW2",
            "session_id": "session_xyz789",
            "overall_score": 75,
            "new_commit": "abc123def456",
        }
        # All string fields should accept strings
        validate(instance=payload, schema=payload_schema)

    def test_new_commit_accepts_strings(self, payload_schema: dict):
        """Test that new_commit field accepts string values."""
        payload = {
            "task_id": "task_abc123",
            "student_id": "student_123",
            "assignment_id": "HW2",
            "session_id": "session_xyz789",
            "overall_score": 75,
            "new_commit": "abc123def456",
        }
        validate(instance=payload, schema=payload_schema)

