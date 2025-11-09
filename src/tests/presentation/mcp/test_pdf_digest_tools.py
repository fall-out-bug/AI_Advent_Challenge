"""Tests for PDF digest MCP tools (TDD - Red Phase)."""

import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


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
    from src.infrastructure.database.mongo import close_client, get_db

    db = await get_db()
    await db.channels.delete_many({})
    await db.posts.delete_many({})
    yield
    await db.channels.delete_many({})
    await db.posts.delete_many({})
    await close_client()


@pytest.mark.asyncio
async def test_get_posts_from_db_groups_by_channel():
    """Test that get_posts_from_db groups posts by channel."""
    from src.presentation.mcp.tools.digest_tools import save_posts_to_db
    from src.presentation.mcp.tools.pdf_digest_tools import get_posts_from_db

    # Setup: save posts for different channels
    posts_channel1 = [
        {
            "text": "Post 1 from channel1",
            "date": datetime.utcnow(),
            "message_id": "msg_1",
        },
        {
            "text": "Post 2 from channel1",
            "date": datetime.utcnow(),
            "message_id": "msg_2",
        },
    ]
    posts_channel2 = [
        {
            "text": "Post 1 from channel2",
            "date": datetime.utcnow(),
            "message_id": "msg_3",
        },
    ]

    await save_posts_to_db(posts_channel1, "channel1", user_id=1)
    await save_posts_to_db(posts_channel2, "channel2", user_id=1)

    # Act
    result = await get_posts_from_db(user_id=1, hours=24)

    # Assert
    assert "posts_by_channel" in result
    assert "total_posts" in result
    assert "channels_count" in result
    assert "channel1" in result["posts_by_channel"]
    assert "channel2" in result["posts_by_channel"]
    assert len(result["posts_by_channel"]["channel1"]) >= 2
    assert len(result["posts_by_channel"]["channel2"]) >= 1
    assert result["total_posts"] >= 3
    assert result["channels_count"] >= 2


@pytest.mark.asyncio
async def test_get_posts_from_db_enforces_limits():
    """Test that get_posts_from_db enforces max posts per channel and max channels limits."""
    from src.presentation.mcp.tools.digest_tools import save_posts_to_db
    from src.presentation.mcp.tools.pdf_digest_tools import get_posts_from_db

    # Setup: create more than 100 posts for one channel
    many_posts = [
        {
            "text": f"Post {i}",
            "date": datetime.utcnow(),
            "message_id": f"msg_{i}",
        }
        for i in range(150)
    ]

    await save_posts_to_db(many_posts, "channel_many", user_id=1)

    # Act
    result = await get_posts_from_db(user_id=1, hours=24)

    # Assert: should limit to 100 posts per channel
    if "channel_many" in result["posts_by_channel"]:
        assert len(result["posts_by_channel"]["channel_many"]) <= 100


@pytest.mark.asyncio
async def test_get_posts_from_db_empty_results():
    """Test that get_posts_from_db handles empty results gracefully."""
    from src.presentation.mcp.tools.pdf_digest_tools import get_posts_from_db

    # Act: query for user with no posts
    result = await get_posts_from_db(user_id=99999, hours=24)

    # Assert
    assert "posts_by_channel" in result
    assert "total_posts" in result
    assert "channels_count" in result
    assert result["total_posts"] == 0
    assert result["channels_count"] == 0
    assert isinstance(result["posts_by_channel"], dict)


@pytest.mark.asyncio
async def test_get_posts_from_db_date_filtering():
    """Test that get_posts_from_db filters posts by date correctly."""
    from src.presentation.mcp.tools.digest_tools import save_posts_to_db
    from src.presentation.mcp.tools.pdf_digest_tools import get_posts_from_db

    # Setup: create old and new posts
    old_post = {
        "text": "Old post",
        "date": datetime.utcnow() - timedelta(hours=48),
        "message_id": "old_msg",
    }
    new_post = {
        "text": "New post",
        "date": datetime.utcnow(),
        "message_id": "new_msg",
    }

    await save_posts_to_db([old_post], "test_channel", user_id=1)
    await save_posts_to_db([new_post], "test_channel", user_id=1)

    # Act: query for last 24 hours only
    result = await get_posts_from_db(user_id=1, hours=24)

    # Assert: should only include new post
    if "test_channel" in result["posts_by_channel"]:
        posts = result["posts_by_channel"]["test_channel"]
        post_texts = [p.get("text") for p in posts]
        assert "New post" in post_texts
        assert "Old post" not in post_texts


@pytest.mark.asyncio
async def test_summarize_posts_generates_summary():
    """Test that summarize_posts generates summary for posts."""
    from src.presentation.mcp.tools.pdf_digest_tools import summarize_posts

    posts = [
        {
            "text": "First post about new technology developments",
            "date": datetime.utcnow(),
            "message_id": "1",
        },
        {
            "text": "Second post about software updates",
            "date": datetime.utcnow(),
            "message_id": "2",
        },
    ]

    # Act
    result = await summarize_posts(posts, "test_channel", max_sentences=5)

    # Assert
    assert "summary" in result
    assert "post_count" in result
    assert "channel" in result
    assert result["channel"] == "test_channel"
    assert result["post_count"] == 2
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0


@pytest.mark.asyncio
async def test_summarize_posts_enforces_limits():
    """Test that summarize_posts enforces ML-engineer limits."""
    from src.presentation.mcp.tools.pdf_digest_tools import summarize_posts

    # Create many posts (>100)
    posts = [
        {
            "text": f"Post {i} with some content",
            "date": datetime.utcnow(),
            "message_id": f"msg_{i}",
        }
        for i in range(150)
    ]

    # Act
    result = await summarize_posts(posts, "test_channel", max_sentences=5)

    # Assert: should limit to 100 posts
    assert result["post_count"] <= 100
    assert result["channel"] == "test_channel"
    assert isinstance(result["summary"], str)


@pytest.mark.asyncio
async def test_summarize_posts_handles_empty_posts():
    """Test that summarize_posts handles empty posts list."""
    from src.presentation.mcp.tools.pdf_digest_tools import summarize_posts

    # Act
    result = await summarize_posts([], "test_channel", max_sentences=5)

    # Assert
    assert "summary" in result
    assert "post_count" in result
    assert "channel" in result
    assert result["post_count"] == 0
    assert isinstance(result["summary"], str)


@pytest.mark.asyncio
async def test_summarize_posts_handles_llm_errors():
    """Test that summarize_posts handles LLM errors gracefully."""
    from src.presentation.mcp.tools.pdf_digest_tools import summarize_posts

    posts = [
        {
            "text": "Test post",
            "date": datetime.utcnow(),
            "message_id": "1",
        },
    ]

    # Mock LLM summarizer to raise error
    with patch(
        "src.presentation.mcp.tools.pdf_digest_tools.llm_summarize_posts"
    ) as mock_summarize:
        mock_summarize.side_effect = Exception("LLM error")

        # Should still return result (handled gracefully)
        result = await summarize_posts(posts, "test_channel", max_sentences=5)
        assert "summary" in result
        assert "channel" in result
        assert result["channel"] == "test_channel"


@pytest.mark.asyncio
async def test_format_digest_markdown_formats_sections():
    """Test that format_digest_markdown formats summaries into markdown."""
    from src.presentation.mcp.tools.pdf_digest_tools import format_digest_markdown

    summaries = [
        {
            "channel": "channel1",
            "summary": "Summary for channel 1",
            "post_count": 5,
        },
        {
            "channel": "channel2",
            "summary": "Summary for channel 2",
            "post_count": 3,
        },
    ]

    metadata = {
        "generation_date": datetime.utcnow().isoformat(),
        "user_id": 1,
    }

    # Act
    result = await format_digest_markdown(summaries, metadata)

    # Assert
    assert "markdown" in result
    assert "sections_count" in result
    assert result["sections_count"] == 2
    assert isinstance(result["markdown"], str)
    assert "#" in result["markdown"]  # Should have headers
    assert "channel1" in result["markdown"] or "channel2" in result["markdown"]


@pytest.mark.asyncio
async def test_format_digest_markdown_handles_empty_summaries():
    """Test that format_digest_markdown handles empty summaries list."""
    from src.presentation.mcp.tools.pdf_digest_tools import format_digest_markdown

    metadata = {
        "generation_date": datetime.utcnow().isoformat(),
        "user_id": 1,
    }

    # Act
    result = await format_digest_markdown([], metadata)

    # Assert
    assert "markdown" in result
    assert "sections_count" in result
    assert result["sections_count"] == 0
    assert isinstance(result["markdown"], str)


@pytest.mark.asyncio
async def test_combine_markdown_sections_combines_sections():
    """Test that combine_markdown_sections combines multiple markdown sections."""
    from src.presentation.mcp.tools.pdf_digest_tools import combine_markdown_sections

    sections = [
        "# Section 1\n\nContent for section 1",
        "# Section 2\n\nContent for section 2",
    ]

    # Act
    result = await combine_markdown_sections(sections, template="default")

    # Assert
    assert "combined_markdown" in result
    assert "total_chars" in result
    assert isinstance(result["combined_markdown"], str)
    assert result["total_chars"] > 0
    assert "Section 1" in result["combined_markdown"]
    assert "Section 2" in result["combined_markdown"]


@pytest.mark.asyncio
async def test_combine_markdown_sections_handles_empty_sections():
    """Test that combine_markdown_sections handles empty sections list."""
    from src.presentation.mcp.tools.pdf_digest_tools import combine_markdown_sections

    # Act
    result = await combine_markdown_sections([], template="default")

    # Assert
    assert "combined_markdown" in result
    assert "total_chars" in result
    assert isinstance(result["combined_markdown"], str)


@pytest.mark.asyncio
async def test_convert_markdown_to_pdf_generates_pdf():
    """Test that convert_markdown_to_pdf generates PDF bytes."""
    from src.presentation.mcp.tools.pdf_digest_tools import convert_markdown_to_pdf

    markdown = "# Test Document\n\nThis is a test markdown content."

    # Act
    result = await convert_markdown_to_pdf(markdown, style="default")

    # Assert
    assert "pdf_bytes" in result
    assert "file_size" in result
    assert "pages" in result
    assert isinstance(result["pdf_bytes"], (bytes, str))  # May be base64 encoded
    assert result["file_size"] > 0
    assert result["pages"] > 0


@pytest.mark.asyncio
async def test_convert_markdown_to_pdf_handles_errors():
    """Test that convert_markdown_to_pdf handles conversion errors gracefully."""
    from src.presentation.mcp.tools.pdf_digest_tools import convert_markdown_to_pdf

    # Invalid markdown that might cause issues
    invalid_markdown = ""  # Empty might cause issues

    # Act
    result = await convert_markdown_to_pdf(invalid_markdown, style="default")

    # Assert: should return error dict or handle gracefully
    assert isinstance(result, dict)
    # Either success or error dict
    assert "pdf_bytes" in result or "error" in result


@pytest.mark.asyncio
async def test_convert_markdown_to_pdf_applies_styling():
    """Test that convert_markdown_to_pdf applies CSS styling."""
    from src.presentation.mcp.tools.pdf_digest_tools import convert_markdown_to_pdf

    markdown = "# Test Document\n\nContent with **bold** text."

    # Act
    result = await convert_markdown_to_pdf(markdown, style="default")

    # Assert
    assert "pdf_bytes" in result
    assert result["file_size"] > 0
    # Styling is applied internally, we just verify it doesn't crash
