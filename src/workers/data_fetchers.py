"""Data fetching utilities for worker notifications."""

from __future__ import annotations

from typing import Any, Optional, Protocol

from src.infrastructure.database.mongo import get_db
from src.infrastructure.monitoring.logger import get_logger
from src.workers.formatters import format_single_digest, format_summary

logger = get_logger(name="data_fetchers")


class MCPClientProtocol(Protocol):
    """Protocol for MCP client."""

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Call a tool with arguments."""
        ...


async def get_summary_text(
    mcp_client: MCPClientProtocol,
    user_id: int,
    timeframe: str = "today",
    debug: bool = False
) -> Optional[str]:
    """Get summary text for user.

    Purpose:
        Fetch task summary data and format it into message text.
        Supports both MCP mode (normal) and direct DB query (debug).

    Args:
        mcp_client: MCP client instance for normal mode
        user_id: User ID
        timeframe: Timeframe for summary ("today", "week", "last_24h")
        debug: If True, query DB directly and use debug formatting

    Returns:
        Formatted summary text or None on error
    """
    try:
        logger.info("get_summary_text called", 
                   user_id=user_id, 
                   timeframe=timeframe, 
                   debug=debug)

        # In debug mode, ALWAYS query DB directly, skip MCP completely
        if debug:
            return await _get_summary_from_db(user_id)

        # Normal mode: use MCP
        logger.info("Calling get_summary tool", 
                   user_id=user_id, 
                   timeframe=timeframe)
        summary = await mcp_client.call_tool(
            "get_summary", 
            {"user_id": user_id, "timeframe": timeframe}
        )
        tasks = summary.get("tasks", [])
        stats = summary.get("stats", {})

        logger.info("Got summary from MCP", 
                   user_id=user_id, 
                   task_count=len(tasks), 
                   stats=stats)

        result = format_summary(tasks, stats, debug=debug)
        logger.info("Formatted summary", 
                   user_id=user_id, 
                   result_length=len(result) if result else 0, 
                   has_result=result is not None)
        return result

    except Exception as e:
        logger.error("Error getting summary text", 
                    user_id=user_id, 
                    error=str(e), 
                    exc_info=True)
        if debug:
            return f"🔍 *Debug Summary Error*\n\nError retrieving summary: {str(e)}"
        return None


async def _get_summary_from_db(user_id: int) -> str:
    """Get summary directly from database (debug mode).

    Args:
        user_id: User ID

    Returns:
        Formatted summary text or error message
    """
    logger.info("🔧 DEBUG MODE: Querying DB directly, skipping MCP", 
               user_id=user_id)
    try:
        db = await get_db()
        user_id_int = int(user_id)

        logger.info("🔧 Executing DB query", user_id=user_id_int)
        raw = await db.tasks.find({"user_id": user_id_int}).to_list(length=200)

        logger.info("🔧 DB returned raw tasks", 
                   user_id=user_id, 
                   raw_count=len(raw))

        tasks_filtered = [t for t in raw if not t.get("completed", False)]

        logger.info("🔧 After filter (completed=False)", 
                   user_id=user_id, 
                   filtered_count=len(tasks_filtered))

        # Normalize for formatter (id field)
        normalized = []
        for t in tasks_filtered:
            td = dict(t)
            if "_id" in td:
                td["id"] = str(td.pop("_id"))
            normalized.append(td)
            logger.info("🔧 Normalized task", 
                       user_id=user_id, 
                       task_title=td.get("title", "No title")[:50])

        tasks = normalized
        stats = {
            "total": len(tasks),
            "completed": 0,
            "overdue": 0,
            "high_priority": sum(1 for t in tasks if t.get("priority") == "high"),
        }

        logger.info("🔧 Final tasks and stats", 
                   user_id=user_id, 
                   task_count=len(tasks), 
                   stats=stats)

        result = format_summary(tasks, stats, debug=True)

        logger.info("🔧 Formatted summary result", 
                   user_id=user_id, 
                   result_length=len(result) if result else 0)
        return result

    except Exception as db_err:
        logger.error("🔧 Debug DB query failed", 
                    user_id=user_id, 
                    error=str(db_err), 
                    exc_info=True)
        import traceback
        logger.error("🔧 Debug DB traceback", 
                    user_id=user_id, 
                    traceback=traceback.format_exc())
        return f"🔍 *Debug Summary Error*\n\nDB query failed: {str(db_err)}"


async def get_digest_texts(
    mcp_client: MCPClientProtocol,
    user_id: int,
    debug: bool = False
) -> list[str]:
    """Get digest texts for user - one per channel.

    Purpose:
        Fetch channel digest data and format into separate messages.
        Returns one message per channel for better readability.

    Args:
        mcp_client: MCP client instance
        user_id: User ID
        debug: If True, use debug formatting (same 24-hour window as normal mode)

    Returns:
        List of digest text messages, one per channel
    """
    try:
        # Always use 24 hours for consistency (both debug and normal mode)
        hours = 24

        logger.info("Calling get_channel_digest tool", 
                   user_id=user_id, 
                   hours=hours,
                   debug=debug)

        digest_data = await mcp_client.call_tool(
            "get_channel_digest", 
            {"user_id": user_id, "hours": hours}
        )

        digests = digest_data.get("digests", [])

        logger.info("Got digest from MCP", 
                   user_id=user_id, 
                   digest_count=len(digests))

        if not digests:
            if debug:
                return [
                    f"📰 Debug Digest (Last 24 hours):\n\n"
                    f"📌 No new posts in subscribed channels."
                ]
            return []  # Return empty list in normal mode (no message sent)

        # Format each channel as a separate message
        results = []
        for digest in digests:
            formatted = format_single_digest(digest, debug=debug)
            if formatted:
                results.append(formatted)

        logger.info("Formatted digest texts", 
                   user_id=user_id, 
                   message_count=len(results))
        return results

    except Exception as e:
        logger.error("Error getting digest texts", 
                    user_id=user_id, 
                    error=str(e), 
                    exc_info=True)
        if debug:
            return [f"📰 Debug Digest Error\n\nError retrieving digest: {str(e)}"]
        return []


async def get_digest_text(
    mcp_client: MCPClientProtocol,
    user_id: int,
    debug: bool = False
) -> Optional[str]:
    """Get single combined digest text for user (legacy method).

    Purpose:
        Get all digest texts combined into one message.
        Kept for compatibility with existing code.

    Args:
        mcp_client: MCP client instance
        user_id: User ID
        debug: If True, use debug formatting and extended time window

    Returns:
        Combined digest text or None if no digests
    """
    texts = await get_digest_texts(mcp_client, user_id, debug=debug)
    if not texts:
        return None
    # Combine all texts with separator
    return "\n\n---\n\n".join(texts)

