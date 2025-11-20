"""Tests for PostRepository with hybrid deduplication (message_id + content_hash)."""

<<<<<<< HEAD
import asyncio
import hashlib
import os
from datetime import datetime, timedelta

import pytest

=======
import hashlib
from datetime import datetime, timedelta

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.infrastructure.repositories.post_repository import PostRepository

>>>>>>> origin/master

pytestmark = pytest.mark.asyncio


<<<<<<< HEAD
@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _set_test_db_env(monkeypatch):
    """Set test database environment variables."""
    monkeypatch.setenv("DB_NAME", "butler_test")
    monkeypatch.setenv(
        "MONGODB_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    )


@pytest.fixture
async def repo():
    """Create PostRepository instance with test database."""
    from src.infrastructure.database.mongo import close_client, get_db
    from src.infrastructure.repositories.post_repository import PostRepository

    db = await get_db()
    repository = PostRepository(db)
    # Cleanup before each test
    await db.posts.delete_many({})
    yield repository
    # Cleanup after
    await db.posts.delete_many({})
    await close_client()
=======
@pytest.fixture
async def repo(mongodb_database_async: AsyncIOMotorDatabase):
    """Create PostRepository instance with per-test database.

    Args:
        mongodb_database_async: Per-test async MongoDB database fixture.

    Returns:
        PostRepository: Repository instance using per-test database.
    """
    repository = PostRepository(mongodb_database_async)
    # Cleanup before each test (per-test DB is already isolated)
    await mongodb_database_async.posts.delete_many({})
    yield repository
    # Cleanup happens automatically via mongodb_database_async fixture
>>>>>>> origin/master


def _create_content_hash(text: str, channel_username: str) -> str:
    """Helper to create content hash for testing."""
    content = f"{text}{channel_username}"
    return hashlib.sha256(content.encode()).hexdigest()


def _create_test_post(
    channel_username: str = "test_channel",
    message_id: str = "123",
    text: str = "Test post",
    user_id: int = 1,
    date: datetime | None = None,
) -> dict:
    """Create test post dictionary."""
    if date is None:
        date = datetime.utcnow()
    content_hash = _create_content_hash(text, channel_username)
    return {
        "channel_username": channel_username,
        "message_id": message_id,
        "content_hash": content_hash,
        "user_id": user_id,
        "text": text,
        "date": date,
        "fetched_at": datetime.utcnow(),
        "views": None,
        "metadata": {},
    }


async def test_save_post_saves_new_post_successfully(repo):
    """Test that save_post saves a new post successfully."""
    post = _create_test_post(
        channel_username="test_channel", message_id="1", text="New post"
    )

    post_id = await repo.save_post(post)

    assert isinstance(post_id, str)
    assert len(post_id) > 0


async def test_save_post_deduplication_by_message_id(repo):
    """Test that save_post prevents duplicates by message_id within 24h window."""
    post1 = _create_test_post(
        channel_username="test_channel",
        message_id="duplicate_123",
        text="Original post",
        date=datetime.utcnow(),
    )

    post2 = _create_test_post(
        channel_username="test_channel",
        message_id="duplicate_123",
        text="Different text but same message_id",
        date=datetime.utcnow(),
    )

    # Save first post
    post_id1 = await repo.save_post(post1)
    assert post_id1 is not None

    # Try to save duplicate - should return None or same ID
    post_id2 = await repo.save_post(post2)
    assert post_id2 is None or post_id2 == post_id1

    # Verify only one post exists
    posts = await repo.get_posts_by_channel(
        "test_channel", since=datetime.utcnow() - timedelta(hours=1)
    )
    assert len(posts) == 1


async def test_save_post_deduplication_by_content_hash(repo):
    """Test that save_post prevents duplicates by content_hash within 7-day window."""
    text = "Same content, different message_id"
    post1 = _create_test_post(
        channel_username="test_channel",
        message_id="msg_1",
        text=text,
        date=datetime.utcnow() - timedelta(days=2),
    )

    post2 = _create_test_post(
        channel_username="test_channel",
        message_id="msg_2",
        text=text,
        date=datetime.utcnow() - timedelta(days=1),
    )

    # Save first post
    post_id1 = await repo.save_post(post1)
    assert post_id1 is not None

    # Try to save duplicate - should return None (content_hash match)
    post_id2 = await repo.save_post(post2)
    assert post_id2 is None

    # Verify only one post exists
    posts = await repo.get_posts_by_channel(
        "test_channel", since=datetime.utcnow() - timedelta(days=8)
    )
    assert len(posts) == 1


async def test_save_post_allows_duplicate_after_message_id_window(repo):
    """Test that duplicate message_id is allowed after 24h window."""
    old_date = datetime.utcnow() - timedelta(hours=25)
    post1 = _create_test_post(
        channel_username="test_channel",
        message_id="old_msg",
        text="Old post",
        date=old_date,
    )

    post2 = _create_test_post(
        channel_username="test_channel",
        message_id="old_msg",
        text="New post with same message_id",
        date=datetime.utcnow(),
    )

    # Save old post
    post_id1 = await repo.save_post(post1)
    assert post_id1 is not None

    # Save new post with same message_id but after 24h - should succeed
    post_id2 = await repo.save_post(post2)
    assert post_id2 is not None
    assert post_id2 != post_id1


async def test_get_posts_by_user_subscriptions_filters_correctly(repo):
    """Test that get_posts_by_user_subscriptions filters by user subscriptions."""
    # Create posts for different users
    post1 = _create_test_post(
        user_id=1, channel_username="channel1", message_id="1", text="User 1 post"
    )
    post2 = _create_test_post(
        user_id=2, channel_username="channel2", message_id="2", text="User 2 post"
    )
    post3 = _create_test_post(
        user_id=1,
        channel_username="channel1",
        message_id="3",
        text="Another User 1 post",
    )

    await repo.save_post(post1)
    await repo.save_post(post2)
    await repo.save_post(post3)

    # Mock channels collection - user 1 subscribes to channel1
<<<<<<< HEAD
    from src.infrastructure.database.mongo import get_db

    db = await get_db()
=======
    # Use the same database as the repository (from repo fixture)
    from motor.motor_asyncio import AsyncIOMotorDatabase

    db: AsyncIOMotorDatabase = repo._db
>>>>>>> origin/master
    await db.channels.insert_one(
        {"user_id": 1, "channel_username": "channel1", "active": True}
    )

    # Get posts for user 1
    posts = await repo.get_posts_by_user_subscriptions(user_id=1, hours=24)
    assert len(posts) == 2
    assert all(p["user_id"] == 1 for p in posts)
    assert all(p["channel_username"] == "channel1" for p in posts)


async def test_get_posts_by_user_subscriptions_empty_subscriptions(repo):
    """Test that get_posts_by_user_subscriptions returns empty list for user with no subscriptions."""
    post = _create_test_post(
        user_id=1, channel_username="channel1", message_id="1", text="Post"
    )
    await repo.save_post(post)

    # User has no subscriptions
    posts = await repo.get_posts_by_user_subscriptions(user_id=999, hours=24)
    assert len(posts) == 0


async def test_get_posts_by_channel_with_date_filtering(repo):
    """Test that get_posts_by_channel filters by date correctly."""
    now = datetime.utcnow()
    old_post = _create_test_post(
        channel_username="test_channel",
        message_id="old",
        text="Old post",
        date=now - timedelta(hours=2),
    )
    new_post = _create_test_post(
        channel_username="test_channel",
        message_id="new",
        text="New post",
        date=now - timedelta(minutes=30),
    )

    await repo.save_post(old_post)
    await repo.save_post(new_post)

    # Get posts from last hour only
    posts = await repo.get_posts_by_channel(
        "test_channel", since=now - timedelta(hours=1)
    )
    assert len(posts) == 1
    assert posts[0]["message_id"] == "new"


async def test_get_posts_by_channel_empty_results(repo):
    """Test that get_posts_by_channel returns empty list when no posts found."""
    posts = await repo.get_posts_by_channel(
        "nonexistent_channel", since=datetime.utcnow() - timedelta(hours=1)
    )
    assert len(posts) == 0


async def test_delete_old_posts_removes_expired_posts(repo):
    """Test that delete_old_posts removes posts older than specified days."""
    now = datetime.utcnow()
    old_post = _create_test_post(
        channel_username="test_channel",
        message_id="old",
        text="Old post",
        date=now - timedelta(days=8),
    )
    new_post = _create_test_post(
        channel_username="test_channel",
        message_id="new",
        text="New post",
        date=now - timedelta(days=2),
    )

    await repo.save_post(old_post)
    await repo.save_post(new_post)

    # Delete posts older than 7 days
    deleted_count = await repo.delete_old_posts(days=7)
    assert deleted_count >= 1

    # Verify old post is deleted, new post remains
    posts = await repo.get_posts_by_channel(
        "test_channel", since=now - timedelta(days=10)
    )
    assert len(posts) == 1
    assert posts[0]["message_id"] == "new"


async def test_save_post_error_handling_invalid_input(repo):
    """Test that save_post handles invalid input gracefully."""
    # Missing required fields
    invalid_post = {"text": "Missing fields"}

    with pytest.raises(ValueError):
        await repo.save_post(invalid_post)


async def test_save_post_edge_case_empty_text(repo):
    """Test that save_post handles empty text."""
    post = _create_test_post(text="", message_id="empty")
    post_id = await repo.save_post(post)
    assert post_id is not None


async def test_get_posts_by_user_subscriptions_time_filtering(repo):
    """Test that get_posts_by_user_subscriptions respects hours parameter."""
    now = datetime.utcnow()

    # Create posts at different times
    old_post = _create_test_post(
        user_id=1,
        channel_username="channel1",
        message_id="old",
        text="Old post",
        date=now - timedelta(hours=25),
    )
    new_post = _create_test_post(
        user_id=1,
        channel_username="channel1",
        message_id="new",
        text="New post",
        date=now - timedelta(hours=5),
    )

    await repo.save_post(old_post)
    await repo.save_post(new_post)

    # Mock channels collection
<<<<<<< HEAD
    from src.infrastructure.database.mongo import get_db

    db = await get_db()
=======
    # Use the same database as the repository (from repo fixture)
    from motor.motor_asyncio import AsyncIOMotorDatabase

    db: AsyncIOMotorDatabase = repo._db
>>>>>>> origin/master
    await db.channels.insert_one(
        {"user_id": 1, "channel_username": "channel1", "active": True}
    )

    # Get posts from last 24 hours
    posts = await repo.get_posts_by_user_subscriptions(user_id=1, hours=24)
    assert len(posts) == 1
    assert posts[0]["message_id"] == "new"


async def test_deduplication_message_id_different_channels(repo):
    """Test that same message_id in different channels is allowed."""
    post1 = _create_test_post(
        channel_username="channel1", message_id="123", text="Post 1"
    )
    post2 = _create_test_post(
        channel_username="channel2", message_id="123", text="Post 2"
    )

    post_id1 = await repo.save_post(post1)
    post_id2 = await repo.save_post(post2)

    assert post_id1 is not None
    assert post_id2 is not None
    assert post_id1 != post_id2
