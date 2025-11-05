"""Channel name resolution MCP tool.

Following Python Zen: Simple is better than complex.
"""

from __future__ import annotations

from typing import Any, Dict

from src.presentation.mcp.server import mcp
from src.application.use_cases.resolve_channel_name import ResolveChannelNameUseCase
from src.infrastructure.logging import get_logger

logger = get_logger("channel_resolution")


@mcp.tool()
async def resolve_channel_name(
    user_id: int,
    input_name: str,
    allow_telegram_search: bool = True,
) -> Dict[str, Any]:
    """Resolve channel name from user input.

    Purpose:
        Resolves user input (channel name, title, username) to actual channel
        by matching against subscribed channels using LLM, and optionally
        searching Telegram if not found.

    Args:
        user_id: Telegram user ID
        input_name: User input (channel name, title, or username)
        allow_telegram_search: Whether to search Telegram if not found in subscriptions

    Returns:
        Dict with resolution information:
        {
            "resolved": true/false,
            "channel_username": "onaboka",
            "channel_title": "Набока",
            "confidence": 0.95,
            "source": "subscription" | "search",
            "reason": "explanation"
        }

    Example:
        >>> result = await resolve_channel_name(123, "Набока")
        >>> result["resolved"]
        True
        >>> result["channel_username"]
        'onaboka'
    """
    logger.info(
        f"Resolving channel name: user_id={user_id}, input={input_name}, "
        f"allow_search={allow_telegram_search}"
    )

    try:
        use_case = ResolveChannelNameUseCase(allow_telegram_search=allow_telegram_search)
        result = await use_case.execute(
            user_id=user_id,
            input_name=input_name,
            allow_telegram_search=allow_telegram_search,
        )

        return {
            "resolved": result.found,
            "channel_username": result.channel_username,
            "channel_title": result.channel_title,
            "confidence": result.confidence_score,
            "source": result.source,
            "reason": result.reason,
        }

    except Exception as e:
        logger.error(
            f"Error resolving channel name: user_id={user_id}, input={input_name}, error={e}",
            exc_info=True,
        )
        return {
            "resolved": False,
            "channel_username": None,
            "channel_title": None,
            "confidence": 0.0,
            "source": "error",
            "reason": f"Error during resolution: {str(e)}",
        }

