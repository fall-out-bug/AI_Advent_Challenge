"""MCP tools for channel digests backed by MongoDB.

This module re-exports all channel tools for backward compatibility.
Tools are organized in submodules for better maintainability.

Following Python Zen:
- Simple is better than complex
- Namespaces are one honking great idea
"""

# Re-export all tools for backward compatibility
from src.presentation.mcp.tools.channels import (
    add_channel,
    list_channels,
    delete_channel,
    get_channel_metadata,
    get_channel_digest,
    get_channel_digest_by_name,
    request_channel_digest_async,
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

