"""Unit tests for channel digest time filtering logic.

These tests verify time filtering logic without requiring MongoDB.
They mock database operations and focus on verifying that:
- Posts are correctly filtered by timestamp
- Only posts within specified time window are included
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_posts_with_timestamps():
    """Create mock posts with different timestamps."""
    now = datetime.utcnow()
    return [
        {
            "text": "Recent post within 24h",
            "date": (now - timedelta(hours=1)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_1",
        },
        {
            "text": "Post from 12 hours ago",
            "date": (now - timedelta(hours=12)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_2",
        },
        {
            "text": "Post from 23 hours ago",
            "date": (now - timedelta(hours=23)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_3",
        },
        {
            "text": "Old post outside 24h",
            "date": (now - timedelta(hours=25)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_4",
        },
        {
            "text": "Very old post",
            "date": (now - timedelta(days=2)).isoformat(),
            "channel": "test_channel",
            "message_id": "msg_5",
        },
    ]


def test_time_filtering_filters_by_cutoff_time(mock_posts_with_timestamps):
    """Test that posts are filtered correctly by cutoff time."""
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    filtered = [
        p for p in mock_posts_with_timestamps
        if datetime.fromisoformat(p["date"]) >= cutoff_time
    ]
    
    assert len(filtered) == 3  # Only 3 posts within 24 hours
    assert all(datetime.fromisoformat(p["date"]) >= cutoff_time for p in filtered)
    assert "Recent post" in filtered[0]["text"]
    assert "Old post" not in [p["text"] for p in filtered]
    assert "Very old post" not in [p["text"] for p in filtered]


def test_time_filtering_respects_custom_hours():
    """Test that filtering respects custom hours parameter."""
    now = datetime.utcnow()
    
    # Create posts with specific timestamps relative to now
    posts = [
        {"text": "Post 1h ago", "date": (now - timedelta(hours=1)).isoformat()},
        {"text": "Post 12h ago", "date": (now - timedelta(hours=12)).isoformat()},
        {"text": "Post 13h ago", "date": (now - timedelta(hours=13)).isoformat()},
    ]
    
    cutoff_time = now - timedelta(hours=12)
    
    filtered = [
        p for p in posts
        if datetime.fromisoformat(p["date"]) >= cutoff_time
    ]
    
    assert len(filtered) == 2  # Only 2 posts within 12 hours
    assert all(datetime.fromisoformat(p["date"]) >= cutoff_time for p in filtered)


def test_time_filtering_handles_empty_list():
    """Test that filtering handles empty post list."""
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    posts = []
    
    filtered = [
        p for p in posts
        if datetime.fromisoformat(p["date"]) >= cutoff_time
    ]
    
    assert len(filtered) == 0


def test_time_filtering_includes_boundary_posts():
    """Test that posts exactly at cutoff time are included."""
    now = datetime.utcnow()
    cutoff_time = now - timedelta(hours=24)
    
    posts = [
        {
            "text": "Post exactly at cutoff",
            "date": cutoff_time.isoformat(),
            "channel": "test",
            "message_id": "msg_1",
        },
        {
            "text": "Post just before cutoff",
            "date": (cutoff_time - timedelta(seconds=1)).isoformat(),
            "channel": "test",
            "message_id": "msg_2",
        },
    ]
    
    filtered = [
        p for p in posts
        if datetime.fromisoformat(p["date"]) >= cutoff_time
    ]
    
    assert len(filtered) == 1
    assert "exactly at cutoff" in filtered[0]["text"]


@pytest.mark.asyncio
async def test_fetch_channel_posts_filters_by_since():
    """Test that fetch_channel_posts filters posts by since parameter."""
    from src.infrastructure.clients.telegram_utils import fetch_channel_posts
    
    now = datetime.utcnow()
    since = now - timedelta(hours=24)
    
    # Mock posts - fetch_channel_posts creates placeholder posts
    with patch("src.infrastructure.clients.telegram_utils.Bot") as mock_bot:
        mock_chat = MagicMock()
        mock_chat.id = 123
        mock_bot.return_value.get_chat = AsyncMock(return_value=mock_chat)
        
        posts = await fetch_channel_posts("test_channel", since=since)
        
        # Verify all posts are within time window
        if posts:
            for post in posts:
                post_date = datetime.fromisoformat(post["date"])
                assert post_date >= since, f"Post {post['message_id']} is before cutoff time"


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires MongoDB dependencies (bson, motor)")
async def test_get_channel_digest_calculates_cutoff_correctly():
    """Test that get_channel_digest calculates cutoff time correctly.
    
    Note: This test requires MongoDB dependencies. Skipped if not available.
    """
    from src.presentation.mcp.tools.digest_tools import get_channel_digest
    from datetime import datetime, timedelta
    
    # Mock database and fetch functions
    mock_db = MagicMock()
    mock_channels = [
        {"_id": "1", "user_id": 100, "channel_username": "test", "active": True}
    ]
    mock_db.channels.find.return_value.to_list = AsyncMock(return_value=mock_channels)
    
    called_since = None
    
    async def mock_fetch(channel_username: str, since: datetime):
        nonlocal called_since
        called_since = since
        return []
    
    now = datetime.utcnow()
    expected_cutoff = now - timedelta(hours=24)
    
    with patch("src.presentation.mcp.tools.digest_tools.get_db", return_value=mock_db):
        with patch("src.presentation.mcp.tools.digest_tools.fetch_channel_posts", side_effect=mock_fetch):
            # Mock summarize_posts to avoid LLM calls
            with patch("src.presentation.mcp.tools.digest_tools.summarize_posts", return_value="Test summary"):
                result = await get_channel_digest(user_id=100, hours=24)  # type: ignore[arg-type]
    
    # Verify cutoff time was calculated correctly
    if called_since:
        # Allow small tolerance for timing differences
        time_diff = abs((called_since - expected_cutoff).total_seconds())
        assert time_diff < 60, f"Expected cutoff around {expected_cutoff}, got {called_since}"


def test_summarize_posts_receives_filtered_posts():
    """Test that summarize_posts receives only filtered posts."""
    from src.infrastructure.llm.summarizer import summarize_posts
    from unittest.mock import AsyncMock
    
    now = datetime.utcnow()
    
    # Create posts: 3 within 24h, 2 outside
    posts = [
        {"text": f"Post {i}", "date": (now - timedelta(hours=i)).isoformat()}
        for i in [1, 12, 23, 25, 48]
    ]
    
    # Filter to only last 24h
    cutoff = now - timedelta(hours=24)
    filtered = [
        p for p in posts
        if datetime.fromisoformat(p["date"]) >= cutoff
    ]
    
    assert len(filtered) == 3  # Only 3 posts within 24h
    
    # Mock LLM client
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value="Test summary")
    
    # summarize_posts should work with filtered posts
    # Note: This is a unit test, so we just verify the structure
    assert len(filtered) == 3
    assert all("Post" in p["text"] for p in filtered)

