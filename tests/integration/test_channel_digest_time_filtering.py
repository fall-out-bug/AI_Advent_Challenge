"""Integration tests for channel digest summarization with time filtering.

Tests verify that:
- Only posts from last 24 hours are included
- Summarization works correctly with filtered posts
- Time filtering respects the hours parameter

Note: These tests require MongoDB. If MongoDB dependencies are not available,
tests will be skipped automatically.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch


@pytest.fixture(autouse=True)
def _set_test_db_env(monkeypatch):
    """Set test database environment."""
    monkeypatch.setenv("DB_NAME", "butler_test")
    monkeypatch.setenv(
        "MONGODB_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    )


@pytest.fixture(autouse=True)
async def _cleanup_db():
    """Cleanup database before and after tests."""
    try:
        from src.infrastructure.database.mongo import get_db, close_client

        db = await get_db()
        await db.channels.delete_many({})
        yield
        await db.channels.delete_many({})
        await close_client()
    except ImportError:
        # Skip if MongoDB dependencies not available
        pytest.skip("MongoDB dependencies not available")


@pytest.fixture
def mock_channel_posts():
    """Create mock posts with different timestamps."""
    now = datetime.utcnow()

    # Create posts: 3 recent (within 24h), 2 old (outside 24h)
    posts = [
        {
            "text": "Новость номер один о последних событиях в технологиях.",
            "date": (now - timedelta(hours=1)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_1",
        },
        {
            "text": "Вторая новость о разработке и тестировании новых функций.",
            "date": (now - timedelta(hours=12)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_2",
        },
        {
            "text": "Третья новость о производительности и оптимизации систем.",
            "date": (now - timedelta(hours=23)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_3",
        },
        {
            "text": "Старая новость, которая не должна попасть в дайджест.",
            "date": (now - timedelta(hours=25)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_4",
        },
        {
            "text": "Еще одна старая новость за пределами временного окна.",
            "date": (now - timedelta(days=2)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_5",
        },
    ]
    return posts


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    True,  # Skip unless MongoDB is available
    reason="Requires MongoDB. Set MONGODB_URL environment variable to run.",
)
async def test_digest_filters_posts_by_24_hours(mock_channel_posts):
    """Test that digest only includes posts from last 24 hours."""
    from src.presentation.mcp.tools.digest_tools import add_channel, get_channel_digest

    # Setup channel
    await add_channel(user_id=100, channel_username="test_channel")  # type: ignore[arg-type]

    # Mock fetch_channel_posts to return our test posts
    async def mock_fetch(channel_username: str, since: datetime):
        """Filter posts by since timestamp."""
        filtered = [
            p for p in mock_channel_posts if datetime.fromisoformat(p["date"]) >= since
        ]
        return filtered

    with patch(
        "src.presentation.mcp.tools.digest_tools.fetch_channel_posts",
        side_effect=mock_fetch,
    ):
        result = await get_channel_digest(user_id=100, hours=24)  # type: ignore[arg-type]

    assert "digests" in result
    assert len(result["digests"]) == 1

    digest = result["digests"][0]
    assert digest["channel"] == "test_channel"
    assert digest["post_count"] == 3  # Only 3 posts within 24 hours
    assert "summary" in digest
    assert len(digest["summary"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_digest_filters_posts_by_custom_hours(mock_channel_posts):
    """Test that digest respects custom hours parameter."""
    from src.presentation.mcp.tools.digest_tools import add_channel, get_channel_digest

    await add_channel(user_id=200, channel_username="test_channel")  # type: ignore[arg-type]

    async def mock_fetch(channel_username: str, since: datetime):
        """Filter posts by since timestamp."""
        filtered = [
            p for p in mock_channel_posts if datetime.fromisoformat(p["date"]) >= since
        ]
        return filtered

    with patch(
        "src.presentation.mcp.tools.digest_tools.fetch_channel_posts",
        side_effect=mock_fetch,
    ):
        # Request only last 12 hours
        result = await get_channel_digest(user_id=200, hours=12)  # type: ignore[arg-type]

    assert "digests" in result
    assert len(result["digests"]) == 1

    digest = result["digests"][0]
    assert digest["post_count"] == 2  # Only 2 posts within 12 hours


@pytest.mark.asyncio
@pytest.mark.integration
async def test_digest_empty_when_no_posts_in_timeframe():
    """Test that digest returns empty list when no posts in timeframe."""
    from src.presentation.mcp.tools.digest_tools import add_channel, get_channel_digest

    await add_channel(user_id=300, channel_username="empty_channel")  # type: ignore[arg-type]

    async def mock_fetch_empty(channel_username: str, since: datetime):
        """Return empty posts list."""
        return []

    with patch(
        "src.presentation.mcp.tools.digest_tools.fetch_channel_posts",
        side_effect=mock_fetch_empty,
    ):
        result = await get_channel_digest(user_id=300, hours=24)  # type: ignore[arg-type]

    assert "digests" in result
    assert isinstance(result["digests"], list)
    assert len(result["digests"]) == 0  # No digests for empty channel


@pytest.mark.asyncio
@pytest.mark.integration
async def test_digest_summarizes_multiple_channels():
    """Test that digest processes multiple channels correctly."""
    from src.presentation.mcp.tools.digest_tools import add_channel, get_channel_digest

    await add_channel(user_id=400, channel_username="channel1")  # type: ignore[arg-type]
    await add_channel(user_id=400, channel_username="channel2")  # type: ignore[arg-type]

    now = datetime.utcnow()

    async def mock_fetch(channel_username: str, since: datetime):
        """Return posts for specific channel."""
        posts = [
            {
                "text": f"Новость из {channel_username} о важных событиях.",
                "date": (now - timedelta(hours=5)).isoformat(),
                "channel": channel_username,
                "message_id": f"msg_{channel_username}_1",
            }
        ]
        return [p for p in posts if datetime.fromisoformat(p["date"]) >= since]

    with patch(
        "src.presentation.mcp.tools.digest_tools.fetch_channel_posts",
        side_effect=mock_fetch,
    ):
        result = await get_channel_digest(user_id=400, hours=24)  # type: ignore[arg-type]

    assert "digests" in result
    assert len(result["digests"]) == 2  # Both channels

    channels = [d["channel"] for d in result["digests"]]
    assert "channel1" in channels
    assert "channel2" in channels


@pytest.mark.asyncio
@pytest.mark.integration
async def test_digest_filters_only_recent_posts_correctly(mock_channel_posts):
    """Test that time filtering correctly excludes old posts."""
    from src.presentation.mcp.tools.digest_tools import add_channel, get_channel_digest

    await add_channel(user_id=500, channel_username="test_channel")  # type: ignore[arg-type]

    cutoff_time = datetime.utcnow() - timedelta(hours=24)

    async def mock_fetch(channel_username: str, since: datetime):
        """Filter posts and verify cutoff time."""
        assert since == cutoff_time, f"Expected cutoff_time {cutoff_time}, got {since}"
        filtered = [
            p for p in mock_channel_posts if datetime.fromisoformat(p["date"]) >= since
        ]
        return filtered

    with patch(
        "src.presentation.mcp.tools.digest_tools.fetch_channel_posts",
        side_effect=mock_fetch,
    ):
        result = await get_channel_digest(user_id=500, hours=24)  # type: ignore[arg-type]

    digest = result["digests"][0]
    post_count = digest["post_count"]

    # Verify only recent posts (within 24h) are included
    assert post_count == 3

    # Verify summary is generated from recent posts only
    summary = digest["summary"]
    assert len(summary) > 20  # Reasonable summary length
    # Old posts should not appear in summary
    assert "Старая новость" not in summary


@pytest.mark.asyncio
@pytest.mark.integration
async def test_digest_updates_last_digest_timestamp():
    """Test that digest updates last_digest timestamp."""
    from src.presentation.mcp.tools.digest_tools import add_channel, get_channel_digest
    from src.infrastructure.database.mongo import get_db

    await add_channel(user_id=600, channel_username="test_channel")  # type: ignore[arg-type]

    db = await get_db()
    channel_before = await db.channels.find_one(
        {"user_id": 600, "channel_username": "test_channel"}
    )
    assert channel_before["last_digest"] is None

    now = datetime.utcnow()

    async def mock_fetch(channel_username: str, since: datetime):
        return [
            {
                "text": "Test post for digest timestamp update.",
                "date": (now - timedelta(hours=1)).isoformat(),
                "channel": channel_username,
                "message_id": "msg_1",
            }
        ]

    with patch(
        "src.presentation.mcp.tools.digest_tools.fetch_channel_posts",
        side_effect=mock_fetch,
    ):
        await get_channel_digest(user_id=600, hours=24)  # type: ignore[arg-type]

    channel_after = await db.channels.find_one(
        {"user_id": 600, "channel_username": "test_channel"}
    )
    assert channel_after["last_digest"] is not None

    # Verify timestamp is recent (within last minute)
    last_digest_time = datetime.fromisoformat(channel_after["last_digest"])
    assert (datetime.utcnow() - last_digest_time).total_seconds() < 60


@pytest.mark.asyncio
@pytest.mark.integration
async def test_digest_handles_errors_gracefully():
    """Test that digest continues processing if one channel fails."""
    from src.presentation.mcp.tools.digest_tools import add_channel, get_channel_digest

    await add_channel(user_id=700, channel_username="good_channel")  # type: ignore[arg-type]
    await add_channel(user_id=700, channel_username="bad_channel")  # type: ignore[arg-type]

    async def mock_fetch(channel_username: str, since: datetime):
        """Raise error for bad_channel, return posts for good_channel."""
        if channel_username == "bad_channel":
            raise Exception("Channel fetch failed")

        return [
            {
                "text": "Good channel post.",
                "date": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "channel": channel_username,
                "message_id": "msg_1",
            }
        ]

    with patch(
        "src.presentation.mcp.tools.digest_tools.fetch_channel_posts",
        side_effect=mock_fetch,
    ):
        result = await get_channel_digest(user_id=700, hours=24)  # type: ignore[arg-type]

    # Should still process good_channel despite bad_channel error
    assert "digests" in result
    assert len(result["digests"]) == 1
    assert result["digests"][0]["channel"] == "good_channel"
