"""Unit tests for UserProfile value object."""

import pytest
from datetime import datetime

from src.domain.personalization.user_profile import UserProfile


def test_create_default_profile():
    """Test default profile creation."""
    profile = UserProfile.create_default_profile("123456789")

    assert profile.user_id == "123456789"
    assert profile.language == "ru"
    assert profile.persona == "Alfred-style дворецкий"
    assert profile.tone == "witty"
    assert profile.preferred_topics == []
    assert profile.memory_summary is None
    assert isinstance(profile.created_at, datetime)
    assert isinstance(profile.updated_at, datetime)


def test_default_profile_immutability():
    """Test that default profile is immutable."""
    profile = UserProfile.create_default_profile("123")

    # Attempting to modify should raise AttributeError
    with pytest.raises(AttributeError):
        profile.user_id = "456"  # type: ignore


def test_profile_validation_empty_user_id():
    """Test validation fails with empty user_id."""
    with pytest.raises(ValueError, match="user_id cannot be empty"):
        UserProfile(
            user_id="",
            language="ru",
            persona="Alfred-style дворецкий",
            tone="witty",
        )


def test_profile_validation_empty_language():
    """Test validation fails with empty language."""
    with pytest.raises(ValueError, match="language cannot be empty"):
        UserProfile(
            user_id="123",
            language="",
            persona="Alfred-style дворецкий",
            tone="witty",
        )


def test_profile_validation_invalid_language():
    """Test validation fails with invalid language."""
    with pytest.raises(ValueError, match="language must be one of"):
        UserProfile(
            user_id="123",
            language="invalid",
            persona="Alfred-style дворецкий",
            tone="witty",
        )


def test_profile_valid_languages():
    """Test that valid languages are accepted."""
    valid_languages = ["ru", "en", "es", "de", "fr"]

    for lang in valid_languages:
        profile = UserProfile(
            user_id="123",
            language=lang,
            persona="Alfred-style дворецкий",
            tone="witty",
        )
        assert profile.language == lang


def test_with_summary():
    """Test with_summary() creates new profile with updated summary."""
    profile = UserProfile.create_default_profile("123")
    summary = "User asked about Python programming"

    updated = profile.with_summary(summary)

    # Original unchanged
    assert profile.memory_summary is None

    # New profile has summary
    assert updated.memory_summary == summary
    assert updated.user_id == profile.user_id
    assert updated.language == profile.language
    assert updated.persona == profile.persona
    assert updated.tone == profile.tone

    # Timestamp updated
    assert updated.updated_at > profile.updated_at


def test_with_summary_immutability():
    """Test that with_summary() returns immutable profile."""
    profile = UserProfile.create_default_profile("123")
    updated = profile.with_summary("New summary")

    # Attempting to modify should raise AttributeError
    with pytest.raises(AttributeError):
        updated.memory_summary = "Modified"  # type: ignore


def test_profile_with_preferred_topics():
    """Test profile with preferred topics."""
    topics = ["Python", "AI", "Machine Learning"]
    profile = UserProfile(
        user_id="123",
        language="ru",
        persona="Alfred-style дворецкий",
        tone="witty",
        preferred_topics=topics,
    )

    assert profile.preferred_topics == topics


def test_profile_equality():
    """Test profile equality based on fields."""
    profile1 = UserProfile.create_default_profile("123")
    profile2 = UserProfile.create_default_profile("123")

    # Different instances, but same data
    assert profile1.user_id == profile2.user_id
    assert profile1.language == profile2.language
    assert profile1.persona == profile2.persona


def test_with_topics():
    """Test updating profile with topics."""
    profile = UserProfile.create_default_profile("123")
    assert profile.preferred_topics == []

    updated = profile.with_topics(["Python", "Docker", "Clean Architecture"])

    assert updated.preferred_topics == ["Python", "Docker", "Clean Architecture"]
    assert updated.user_id == profile.user_id
    assert updated.language == profile.language
    assert updated.persona == profile.persona
    assert updated.tone == profile.tone
    assert updated.memory_summary == profile.memory_summary
    assert updated.created_at == profile.created_at
    assert updated.updated_at > profile.updated_at


def test_with_topics_immutable():
    """Test that with_topics creates new instance."""
    profile = UserProfile.create_default_profile("123")
    updated = profile.with_topics(["Python"])

    assert profile is not updated
    assert profile.preferred_topics == []
    assert updated.preferred_topics == ["Python"]
