"""Unit tests for GodAgentProfile entity."""

import pytest

from src.domain.god_agent.entities.god_agent_profile import GodAgentProfile
from src.domain.god_agent.value_objects.skill import SkillType


def test_god_agent_profile_creation():
    """Test GodAgentProfile creation."""
    profile = GodAgentProfile(
        user_id="user1",
        preferred_skills=[SkillType.CONCIERGE, SkillType.RESEARCH],
        language="en",
    )

    assert profile.user_id == "user1"
    assert len(profile.preferred_skills) == 2
    assert profile.language == "en"


def test_god_agent_profile_preferences_validation():
    """Test GodAgentProfile preferences validation."""
    # Empty preferred_skills is allowed
    profile = GodAgentProfile(
        user_id="user1",
        preferred_skills=[],
        language="en",
    )
    assert profile.preferred_skills == []

    # All skill types are valid
    all_skills = list(SkillType)
    profile = GodAgentProfile(
        user_id="user1",
        preferred_skills=all_skills,
        language="en",
    )
    assert len(profile.preferred_skills) == len(all_skills)


def test_god_agent_profile_language_validation():
    """Test GodAgentProfile language validation."""
    profile = GodAgentProfile(
        user_id="user1",
        preferred_skills=[],
        language="ru",
    )
    assert profile.language == "ru"

    profile = GodAgentProfile(
        user_id="user1",
        preferred_skills=[],
        language="en",
    )
    assert profile.language == "en"
