"""Channel management MCP tools module.

This module provides tools for managing Telegram channel subscriptions,
digests, and posts.
"""

from src.presentation.mcp.tools.channels.channel_management import (
    add_channel,
    list_channels,
    delete_channel,
)
from src.presentation.mcp.tools.channels.channel_metadata import (
    get_channel_metadata,
)
from src.presentation.mcp.tools.channels.channel_digest import (
    get_channel_digest,
    get_channel_digest_by_name,
)
from src.presentation.mcp.tools.channels.posts_management import (
    get_posts,
    collect_posts,
    save_posts_to_db,
)

__all__ = [
    "add_channel",
    "list_channels",
    "delete_channel",
    "get_channel_metadata",
    "get_channel_digest",
    "get_channel_digest_by_name",
    "get_posts",
    "collect_posts",
    "save_posts_to_db",
]

