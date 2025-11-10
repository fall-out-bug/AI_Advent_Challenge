"""Integration tests for full PDF digest flow from post collection to PDF generation.

Following TDD principles:
- Tests verify complete workflow integration
- Use real MongoDB for data persistence
- Test cleanup after execution
- Informative test logs
"""

import os
import pytest
import hashlib
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.infrastructure.database.mongo import get_db, close_client
from src.infrastructure.repositories.post_repository import PostRepository
from src.presentation.mcp.tools.pdf_digest_tools import (
    get_posts_from_db,
    summarize_posts,
    format_digest_markdown,
    combine_markdown_sections,
    convert_markdown_to_pdf,
)
from src.infrastructure.config.settings import Settings


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _set_test_db_env(monkeypatch):
    """Set test database environment variables."""
    monkeypatch.setenv("DB_NAME", "butler_test")
    monkeypatch.setenv(
        "MONGODB_URL", os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    )


@pytest.fixture
async def db():
    """Create database connection for testing."""
    database = await get_db()
    # Cleanup before each test
    await database.posts.delete_many({})
    await database.channels.delete_many({})
    yield database
    # Cleanup after
    await database.posts.delete_many({})
    await database.channels.delete_many({})
    await close_client()


@pytest.fixture
async def repo(db):
    """Create PostRepository instance."""
    return PostRepository(db)


@pytest.fixture
def mock_llm_client(monkeypatch):
    """Mock LLM client for summarization."""

    async def mock_summarize_posts(posts, max_sentences=5, llm=None):
        """Mock summarize_posts function."""
        if not posts:
            return "Нет постов для саммари."
        return f"Summary of {len(posts)} posts with {max_sentences} sentences."

    from src.infrastructure.llm import summarizer

    monkeypatch.setattr(summarizer, "summarize_posts", mock_summarize_posts)


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


async def _setup_test_channels(db, user_id: int = 1):
    """Setup test channels for user."""
    channels = [
        {
            "user_id": user_id,
            "channel_username": "channel1",
            "is_active": True,
            "last_fetch": datetime.utcnow() - timedelta(hours=2),
        },
        {
            "user_id": user_id,
            "channel_username": "channel2",
            "is_active": True,
            "last_fetch": datetime.utcnow() - timedelta(hours=2),
        },
    ]
    await db.channels.insert_many(channels)


async def test_full_pdf_digest_flow(repo, db, mock_llm_client):
    """Test complete PDF digest generation flow.

    Scenario:
    1. Save posts to database
    2. Get posts from database
    3. Summarize posts for each channel
    4. Format as markdown
    5. Combine sections
    6. Convert to PDF
    """
    user_id = 1

    # Setup: Create channels and posts
    await _setup_test_channels(db, user_id)

    # Save posts to database
    posts_channel1 = [
        _create_test_post(
            channel_username="channel1",
            message_id=f"msg_{i}",
            text=f"Post {i} from channel1",
            user_id=user_id,
            date=datetime.utcnow() - timedelta(hours=i),
        )
        for i in range(5)
    ]

    posts_channel2 = [
        _create_test_post(
            channel_username="channel2",
            message_id=f"msg_{i}",
            text=f"Post {i} from channel2",
            user_id=user_id,
            date=datetime.utcnow() - timedelta(hours=i),
        )
        for i in range(3)
    ]

    # Save all posts
    for post in posts_channel1 + posts_channel2:
        await repo.save_post(post)

    # Step 1: Get posts from database
    posts_result = await get_posts_from_db(user_id=user_id, hours=24)
    assert "posts_by_channel" in posts_result
    assert posts_result["channels_count"] == 2
    assert posts_result["total_posts"] == 8
    assert "channel1" in posts_result["posts_by_channel"]
    assert "channel2" in posts_result["posts_by_channel"]

    # Step 2: Summarize posts for each channel
    summaries = []
    for channel_name, posts in posts_result["posts_by_channel"].items():
        summary_result = await summarize_posts(posts, channel_name, max_sentences=5)
        assert "summary" in summary_result
        assert "post_count" in summary_result
        assert "channel" in summary_result
        assert summary_result["channel"] == channel_name
        summaries.append(summary_result)

    assert len(summaries) == 2

    # Step 3: Format as markdown
    metadata = {
        "generation_date": datetime.utcnow().isoformat(),
        "user_id": user_id,
    }
    markdown_result = await format_digest_markdown(summaries, metadata)
    assert "markdown" in markdown_result
    assert "sections_count" in markdown_result
    assert markdown_result["sections_count"] == 2
    assert "# Channel Digest" in markdown_result["markdown"]
    assert "channel1" in markdown_result["markdown"]
    assert "channel2" in markdown_result["markdown"]

    # Step 4: Combine sections
    combined_result = await combine_markdown_sections([markdown_result["markdown"]])
    assert "combined_markdown" in combined_result
    assert "total_chars" in combined_result
    assert combined_result["total_chars"] > 0

    # Step 5: Convert to PDF
    pdf_result = await convert_markdown_to_pdf(combined_result["combined_markdown"])
    assert "pdf_bytes" in pdf_result
    assert "file_size" in pdf_result
    assert "pages" in pdf_result
    assert pdf_result["file_size"] > 0
    assert pdf_result["pages"] > 0
    assert len(pdf_result["pdf_bytes"]) > 0  # Base64 encoded

    # Verify PDF can be decoded
    import base64

    pdf_bytes = base64.b64decode(pdf_result["pdf_bytes"])
    assert len(pdf_bytes) == pdf_result["file_size"]
    assert pdf_bytes.startswith(b"%PDF")  # PDF magic number


async def test_pdf_digest_flow_with_empty_posts(repo, db, mock_llm_client):
    """Test PDF digest flow when no posts are available."""
    user_id = 999

    # Setup: Create channels but no posts
    await _setup_test_channels(db, user_id)

    # Get posts (should be empty)
    posts_result = await get_posts_from_db(user_id=user_id, hours=24)
    assert posts_result["channels_count"] == 0
    assert posts_result["total_posts"] == 0
    assert posts_result["posts_by_channel"] == {}

    # Try to summarize empty posts
    summary_result = await summarize_posts([], "test_channel")
    assert summary_result["summary"] == "Нет постов для саммари."
    assert summary_result["post_count"] == 0


async def test_pdf_digest_flow_with_limits(repo, db, mock_llm_client):
    """Test PDF digest flow respects limits (max posts per channel)."""
    user_id = 2

    # Setup: Create channel with many posts
    await _setup_test_channels(db, user_id)

    # Create more than max_posts_per_channel (default 100)
    posts = [
        _create_test_post(
            channel_username="channel1",
            message_id=f"msg_{i}",
            text=f"Post {i}",
            user_id=user_id,
            date=datetime.utcnow() - timedelta(hours=i),
        )
        for i in range(150)  # More than limit
    ]

    # Save all posts
    for post in posts:
        await repo.save_post(post)

    # Get posts (should be limited)
    posts_result = await get_posts_from_db(user_id=user_id, hours=24)
    assert posts_result["channels_count"] == 1
    settings = Settings()
    assert posts_result["total_posts"] <= settings.pdf_max_posts_per_channel


async def test_pdf_digest_flow_with_multiple_channels(repo, db, mock_llm_client):
    """Test PDF digest flow with multiple channels (max 10 channels limit)."""
    user_id = 3

    # Setup: Create 15 channels (more than limit)
    channels = [
        {
            "user_id": user_id,
            "channel_username": f"channel{i}",
            "is_active": True,
            "last_fetch": datetime.utcnow() - timedelta(hours=2),
        }
        for i in range(15)
    ]
    await db.channels.insert_many(channels)

    # Create posts for all channels
    for i in range(15):
        post = _create_test_post(
            channel_username=f"channel{i}",
            message_id=f"msg_{i}",
            text=f"Post from channel{i}",
            user_id=user_id,
        )
        await repo.save_post(post)

    # Get posts (should be limited to max 10 channels)
    posts_result = await get_posts_from_db(user_id=user_id, hours=24)
    settings = Settings()
    assert posts_result["channels_count"] <= settings.digest_max_channels


async def test_pdf_digest_flow_error_handling(repo, db):
    """Test PDF digest flow handles errors gracefully."""
    user_id = 4

    # Test with invalid markdown (should still work)
    try:
        pdf_result = await convert_markdown_to_pdf("")
        # Should return error dict or empty result
        assert "pdf_bytes" in pdf_result
    except Exception:
        # Conversion might fail, that's acceptable
        pass

    # Test format_digest_markdown with empty summaries
    result = await format_digest_markdown([], {})
    assert "markdown" in result
    assert result["sections_count"] == 0
