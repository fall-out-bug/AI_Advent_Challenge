"""Unit tests for SkillResult entity."""

import pytest

from src.domain.god_agent.entities.skill_result import SkillResult, SkillResultStatus


def test_skill_result_creation_success():
    """Test SkillResult creation with success status."""
    result = SkillResult(
        result_id="result1",
        status=SkillResultStatus.SUCCESS,
        output={"result": "Task completed"},
    )

    assert result.result_id == "result1"
    assert result.status == SkillResultStatus.SUCCESS
    assert result.output == {"result": "Task completed"}
    assert result.error is None


def test_skill_result_creation_failure():
    """Test SkillResult creation with failure status."""
    result = SkillResult(
        result_id="result1",
        status=SkillResultStatus.FAILURE,
        error="Task failed: timeout",
    )

    assert result.status == SkillResultStatus.FAILURE
    assert result.error == "Task failed: timeout"
    assert result.output is None


def test_skill_result_validation_success_requires_output():
    """Test SkillResult validation - success requires output."""
    with pytest.raises(ValueError, match="SUCCESS status requires output"):
        SkillResult(
            result_id="result1",
            status=SkillResultStatus.SUCCESS,
            output=None,
        )


def test_skill_result_validation_failure_requires_error():
    """Test SkillResult validation - failure requires error."""
    with pytest.raises(ValueError, match="FAILURE status requires error"):
        SkillResult(
            result_id="result1",
            status=SkillResultStatus.FAILURE,
            error=None,
        )


def test_skill_result_metadata():
    """Test SkillResult metadata."""
    result = SkillResult(
        result_id="result1",
        status=SkillResultStatus.SUCCESS,
        output={"result": "Task completed"},
        metadata={"latency_ms": 150, "tokens_used": 1000},
    )

    assert result.metadata == {"latency_ms": 150, "tokens_used": 1000}
