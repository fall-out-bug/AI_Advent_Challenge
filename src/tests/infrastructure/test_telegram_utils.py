import pytest
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_fetch_channel_posts_returns_list():
    from src.infrastructure.clients.telegram_utils import fetch_channel_posts

    since = datetime.utcnow() - timedelta(hours=24)
    posts = await fetch_channel_posts("test_channel", since=since)
    assert isinstance(posts, list)


@pytest.mark.asyncio
async def test_fetch_channel_posts_handles_empty_channel():
    from src.infrastructure.clients.telegram_utils import fetch_channel_posts

    since = datetime.utcnow() - timedelta(hours=24)
    posts = await fetch_channel_posts("nonexistent_channel", since=since)
    assert posts == []

