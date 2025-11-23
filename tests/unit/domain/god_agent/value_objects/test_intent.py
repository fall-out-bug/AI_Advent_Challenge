"""Unit tests for Intent value object."""

import pytest

from src.domain.god_agent.value_objects.intent import Intent, IntentType


def test_intent_creation():
    """Test Intent creation with valid values."""
    intent = Intent(
        intent_type=IntentType.CONCIERGE,
        confidence=0.85,
    )

    assert intent.intent_type == IntentType.CONCIERGE
    assert intent.confidence == 0.85


def test_intent_confidence_validation_lower_bound():
    """Test Intent confidence validation - lower bound."""
    with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
        Intent(intent_type=IntentType.CONCIERGE, confidence=-0.1)


def test_intent_confidence_validation_upper_bound():
    """Test Intent confidence validation - upper bound."""
    with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
        Intent(intent_type=IntentType.CONCIERGE, confidence=1.1)


def test_intent_confidence_boundary_values():
    """Test Intent confidence boundary values."""
    intent_min = Intent(intent_type=IntentType.CONCIERGE, confidence=0.0)
    assert intent_min.confidence == 0.0

    intent_max = Intent(intent_type=IntentType.CONCIERGE, confidence=1.0)
    assert intent_max.confidence == 1.0


def test_intent_all_types():
    """Test Intent with all intent types."""
    for intent_type in IntentType:
        intent = Intent(intent_type=intent_type, confidence=0.75)
        assert intent.intent_type == intent_type
        assert intent.confidence == 0.75


def test_intent_immutability():
    """Test Intent immutability."""
    intent = Intent(intent_type=IntentType.RESEARCH, confidence=0.9)

    with pytest.raises(AttributeError):
        intent.intent_type = IntentType.BUILD  # type: ignore

    with pytest.raises(AttributeError):
        intent.confidence = 0.5  # type: ignore
