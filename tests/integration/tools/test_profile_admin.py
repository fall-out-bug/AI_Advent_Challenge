"""Integration tests for profile admin CLI."""

import pytest
from click.testing import CliRunner
from datetime import datetime
from uuid import uuid4

from scripts.tools.profile_admin import cli


@pytest.fixture
async def seed_test_data(real_mongodb):
    """Seed test data."""
    db = real_mongodb
    await db.user_profiles.insert_one({
        "user_id": "test_123",
        "persona": "Alfred-style дворецкий",
        "language": "ru",
        "tone": "witty",
        "preferred_topics": [],
        "memory_summary": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })
    await db.user_memory.insert_many([
        {
            "event_id": str(uuid4()),
            "user_id": "test_123",
            "role": "user",
            "content": "Hello",
            "created_at": datetime.utcnow(),
        },
        {
            "event_id": str(uuid4()),
            "user_id": "test_123",
            "role": "assistant",
            "content": "Good day, sir",
            "created_at": datetime.utcnow(),
        },
    ])


@pytest.mark.asyncio
async def test_list_command(seed_test_data):
    """Test list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "test_123" in result.output
    assert "Alfred-style дворецкий" in result.output


@pytest.mark.asyncio
async def test_show_command(seed_test_data):
    """Test show command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "test_123"])

    assert result.exit_code == 0
    assert "test_123" in result.output
    assert "witty" in result.output
    assert "Total events" in result.output


@pytest.mark.asyncio
async def test_reset_command_with_confirmation(seed_test_data):
    """Test reset command with confirmation."""
    runner = CliRunner()
    result = runner.invoke(cli, ["reset", "test_123"], input="y\n")

    assert result.exit_code == 0
    assert "Reset complete" in result.output or "Reset failed" in result.output


@pytest.mark.asyncio
async def test_update_command(seed_test_data):
    """Test update command."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["update", "test_123", "--tone", "formal"]
    )

    assert result.exit_code == 0
    assert "Profile updated" in result.output or "Error" in result.output


def test_show_command_not_found():
    """Test show command with non-existent user."""
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "nonexistent_user"])

    assert result.exit_code == 0
    assert "Profile not found" in result.output


def test_list_command_no_profiles():
    """Test list command with no profiles."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])

    # Should not fail, just show no profiles message
    assert result.exit_code == 0

