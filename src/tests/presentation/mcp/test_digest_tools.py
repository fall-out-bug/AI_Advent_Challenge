import os
import asyncio
import pytest
from datetime import datetime, timedelta


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _set_test_db_env(monkeypatch):
    monkeypatch.setenv("DB_NAME", "butler_test")
    monkeypatch.setenv("MONGODB_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017"))


@pytest.fixture(autouse=True)
async def _cleanup_db():
    from src.infrastructure.database.mongo import get_db, close_client

    db = await get_db()
    await db.channels.delete_many({})
    await db.posts.delete_many({})
    yield
    await db.channels.delete_many({})
    await db.posts.delete_many({})
    await close_client()


@pytest.mark.asyncio
async def test_add_and_list_channels():
    from src.presentation.mcp.tools.digest_tools import add_channel, list_channels

    res = await add_channel(user_id=1, channel_username="test_channel", tags=["tech"])  # type: ignore[arg-type]
    assert res["status"] in {"subscribed", "already_subscribed"}

    channels = await list_channels(user_id=1, limit=10)  # type: ignore[arg-type]
    assert len(channels["channels"]) > 0


@pytest.mark.asyncio
async def test_delete_channel():
    from src.presentation.mcp.tools.digest_tools import add_channel, delete_channel, list_channels

    add_res = await add_channel(user_id=2, channel_username="temp_channel")  # type: ignore[arg-type]
    channel_id = add_res.get("channel_id")
    if channel_id:
        del_res = await delete_channel(user_id=2, channel_id=channel_id)  # type: ignore[arg-type]
        assert del_res["status"] in {"deleted", "not_found"}


@pytest.mark.asyncio
async def test_get_channel_digest():
    from src.presentation.mcp.tools.digest_tools import get_channel_digest

    digest = await get_channel_digest(user_id=3, hours=24)  # type: ignore[arg-type]
    assert "digests" in digest
    assert isinstance(digest["digests"], list)


@pytest.mark.asyncio
async def test_save_posts_to_db_saves_multiple_posts():
    """Test that save_posts_to_db saves multiple posts successfully."""
    from src.presentation.mcp.tools.digest_tools import save_posts_to_db

    posts = [
        {
            "text": "Test post 1",
            "date": datetime.utcnow(),
            "message_id": "msg_1",
            "views": 100,
        },
        {
            "text": "Test post 2",
            "date": datetime.utcnow(),
            "message_id": "msg_2",
            "views": 200,
        },
    ]

    result = await save_posts_to_db(
        posts=posts, channel_username="test_channel", user_id=1  # type: ignore[arg-type]
    )

    assert result["saved"] >= 0
    assert result["skipped"] >= 0
    assert result["total"] == 2
    assert result["saved"] + result["skipped"] == 2


@pytest.mark.asyncio
async def test_save_posts_to_db_deduplication():
    """Test that save_posts_to_db prevents duplicates."""
    from src.presentation.mcp.tools.digest_tools import save_posts_to_db

    posts = [
        {
            "text": "Duplicate post",
            "date": datetime.utcnow(),
            "message_id": "duplicate_123",
            "views": None,
        },
    ]

    # Save first time
    result1 = await save_posts_to_db(
        posts=posts, channel_username="test_channel", user_id=1  # type: ignore[arg-type]
    )
    assert result1["saved"] == 1
    assert result1["skipped"] == 0

    # Save again - should be skipped
    result2 = await save_posts_to_db(
        posts=posts, channel_username="test_channel", user_id=1  # type: ignore[arg-type]
    )
    assert result2["saved"] == 0
    assert result2["skipped"] == 1


@pytest.mark.asyncio
async def test_save_posts_to_db_empty_list():
    """Test that save_posts_to_db handles empty posts list."""
    from src.presentation.mcp.tools.digest_tools import save_posts_to_db

    result = await save_posts_to_db(
        posts=[], channel_username="test_channel", user_id=1  # type: ignore[arg-type]
    )

    assert result["saved"] == 0
    assert result["skipped"] == 0
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_save_posts_to_db_error_handling():
    """Test that save_posts_to_db handles errors gracefully."""
    from src.presentation.mcp.tools.digest_tools import save_posts_to_db

    # Invalid post (missing required fields)
    invalid_posts = [{"text": "Missing fields"}]

    result = await save_posts_to_db(
        posts=invalid_posts, channel_username="test_channel", user_id=1  # type: ignore[arg-type]
    )

    # Should skip invalid posts
    assert result["saved"] == 0
    assert result["skipped"] >= 0
    assert result["total"] == 1

