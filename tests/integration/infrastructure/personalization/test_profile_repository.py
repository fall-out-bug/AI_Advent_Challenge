"""Integration tests for MongoUserProfileRepository."""

import pytest

from src.domain.personalization.user_profile import UserProfile


@pytest.mark.asyncio
async def test_get_creates_default_profile(profile_repo):
    """Test that get() auto-creates default profile."""
    user_id = "test_user_123"

    # Get profile (should auto-create)
    profile = await profile_repo.get(user_id)

    assert profile is not None
    assert profile.user_id == user_id
    assert profile.persona == "Alfred-style дворецкий"
    assert profile.language == "ru"
    assert profile.tone == "witty"


@pytest.mark.asyncio
async def test_save_and_get_profile(profile_repo):
    """Test save and retrieve profile."""
    user_id = "test_user_456"
    profile = UserProfile.create_default_profile(user_id)

    # Save profile
    await profile_repo.save(profile)

    # Retrieve and verify
    retrieved = await profile_repo.get(user_id)
    assert retrieved is not None
    assert retrieved.user_id == profile.user_id
    assert retrieved.persona == profile.persona
    assert retrieved.language == profile.language
    assert retrieved.tone == profile.tone


@pytest.mark.asyncio
async def test_save_updates_existing_profile(profile_repo):
    """Test that save() updates existing profile."""
    user_id = "test_user_789"

    # Create and save initial profile
    profile = UserProfile.create_default_profile(user_id)
    await profile_repo.save(profile)

    # Update with summary
    updated_profile = profile.with_summary("User asked about Python")
    await profile_repo.save(updated_profile)

    # Retrieve and verify update
    retrieved = await profile_repo.get(user_id)
    assert retrieved is not None
    assert retrieved.memory_summary == "User asked about Python"
    assert retrieved.updated_at > profile.updated_at


@pytest.mark.asyncio
async def test_reset_profile(profile_repo):
    """Test reset profile to defaults."""
    user_id = "test_user_reset"

    # Create profile with custom summary
    profile = UserProfile.create_default_profile(user_id)
    profile_with_summary = profile.with_summary("Custom summary")
    await profile_repo.save(profile_with_summary)

    # Reset
    await profile_repo.reset(user_id)

    # Verify reset to defaults
    reset_profile = await profile_repo.get(user_id)
    assert reset_profile is not None
    assert reset_profile.memory_summary is None
    assert reset_profile.persona == "Alfred-style дворецкий"
    assert reset_profile.language == "ru"
    assert reset_profile.tone == "witty"


@pytest.mark.asyncio
async def test_get_same_user_returns_same_profile(profile_repo):
    """Test that multiple get() calls return same profile."""
    user_id = "test_user_consistent"

    # First get (creates)
    profile1 = await profile_repo.get(user_id)

    # Second get (retrieves)
    profile2 = await profile_repo.get(user_id)

    assert profile1.user_id == profile2.user_id
    assert profile1.persona == profile2.persona
    assert profile1.language == profile2.language
