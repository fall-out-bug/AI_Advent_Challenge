"""Unit tests for SafetyViolation entity."""

import pytest

from src.domain.god_agent.entities.safety_violation import SafetyViolation, VetoRuleType


def test_safety_violation_creation():
    """Test SafetyViolation creation."""
    violation = SafetyViolation(
        violation_id="violation1",
        veto_rule=VetoRuleType.UNTESTABLE_REQUIREMENT,
        message="Requirement cannot be tested",
    )

    assert violation.violation_id == "violation1"
    assert violation.veto_rule == VetoRuleType.UNTESTABLE_REQUIREMENT
    assert violation.message == "Requirement cannot be tested"


def test_safety_violation_all_veto_rules():
    """Test SafetyViolation with all veto rule types."""
    veto_rules = [
        VetoRuleType.UNTESTABLE_REQUIREMENT,
        VetoRuleType.IMPOSSIBLE_STAGING,
        VetoRuleType.MISSING_ROLLBACK_PLAN,
        VetoRuleType.TASK_OVER_4H,
        VetoRuleType.UNDEFINED_DEPENDENCIES,
    ]

    for veto_rule in veto_rules:
        violation = SafetyViolation(
            violation_id=f"violation_{veto_rule.value}",
            veto_rule=veto_rule,
            message=f"Violation: {veto_rule.value}",
        )
        assert violation.veto_rule == veto_rule


def test_safety_violation_context():
    """Test SafetyViolation with context."""
    violation = SafetyViolation(
        violation_id="violation1",
        veto_rule=VetoRuleType.TASK_OVER_4H,
        message="Task estimated at 5 hours",
        context={"task_id": "task1", "estimated_hours": 5.0},
    )

    assert violation.context == {"task_id": "task1", "estimated_hours": 5.0}
