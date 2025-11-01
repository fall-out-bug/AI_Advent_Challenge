"""Function-calling tools schema for the agent.

This registry defines the JSON schema to pass in `tools=` to the
OpenAI-compatible chat endpoint. Keep names stable and descriptions
concise. This is distinct from MCP discovery used for execution.
"""

from __future__ import annotations

from typing import List, Dict, Any


TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_channel_digest_by_name",
            "description": "Get digest of posts from a specific Telegram channel for N days",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {
                        "type": "string",
                        "description": "Human or username form (e.g., 'onaboka' or '@onaboka')",
                        "minLength": 1,
                        "maxLength": 100,
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (1-30)",
                        "minimum": 1,
                        "maximum": 30,
                    },
                },
                "required": ["channel_name", "days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_channels",
            "description": "List all subscribed Telegram channels for the user",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_channel_metadata",
            "description": "Get basic information about a specific channel",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {
                        "type": "string",
                        "description": "Channel username or human name",
                    }
                },
                "required": ["channel_name"],
            },
        },
    },
]


