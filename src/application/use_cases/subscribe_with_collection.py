"""Use case for subscribing to channel with immediate post collection.

Following Clean Architecture: Application layer orchestrates MCP tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from src.infrastructure.logging import get_logger

logger = get_logger("use_cases.subscribe_with_collection")


class MCPClientProtocol(Protocol):
    """Protocol for MCP client."""

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool with arguments."""
        ...


@dataclass
class SubscribeWithCollectionResult:
    """Result of subscribe with collection operation.

    Attributes:
        status: Subscription status ("subscribed", "already_subscribed", "error")
        channel_username: Channel username
        collected_count: Number of posts collected (0 if failed)
        error: Error message if operation failed
    """

    status: str
    channel_username: str
    collected_count: int = 0
    error: Optional[str] = None


class SubscribeToChannelWithCollectionUseCase:
    """Use case for subscribing to channel and immediately collecting posts.

    Purpose:
        Subscribes user to a channel via MCP tool, then immediately
        collects posts (72h, fallback 7d) for immediate digest availability.

    Attributes:
        mcp_client: MCP client for calling tools
    """

    def __init__(
        self,
        mcp_client: MCPClientProtocol | None = None,
    ) -> None:
        """Initialize subscribe with collection use case.

        Args:
            mcp_client: MCP client instance (must be provided)
        """
        if mcp_client is None:
            raise ValueError("mcp_client is required")
        self._mcp = mcp_client

    async def execute(
        self,
        user_id: int,
        channel_username: str,
        hours: int = 72,
        fallback_to_7_days: bool = True,
    ) -> SubscribeWithCollectionResult:
        """Execute subscription with immediate post collection.

        Purpose:
            Subscribe to channel, then collect posts immediately.
            If collection fails, subscription still succeeds.

        Args:
            user_id: Telegram user ID
            channel_username: Channel username without @
            hours: Hours to look back for posts (default 72)
            fallback_to_7_days: If True, retry with 7 days if no posts found

        Returns:
            SubscribeWithCollectionResult with status and collected count
        """
        channel_username = channel_username.lstrip("@")

        try:
            # Step 1: Subscribe to channel
            logger.info(
                f"Subscribing to channel: user_id={user_id}, channel={channel_username}"
            )
            subscribe_result = await self._mcp.call_tool(
                "add_channel",
                {
                    "user_id": user_id,
                    "channel_username": channel_username,
                },
            )

            status = subscribe_result.get("status", "unknown")

            # If subscription failed, return error
            if status == "error":
                error_msg = subscribe_result.get(
                    "message",
                    subscribe_result.get("error", "Unknown subscription error"),
                )
                logger.warning(
                    f"Subscription failed: user_id={user_id}, "
                    f"channel={channel_username}, error={error_msg}"
                )
                return SubscribeWithCollectionResult(
                    status="error",
                    channel_username=channel_username,
                    collected_count=0,
                    error=error_msg,
                )

            # Step 2: Collect posts (if subscribed or already subscribed)
            if status in ("subscribed", "already_subscribed"):
                logger.info(
                    f"Collecting posts for channel: user_id={user_id}, "
                    f"channel={channel_username}, hours={hours}"
                )
                try:
                    # Handle timeout for post collection
                    import asyncio

                    try:
                        collect_result = await asyncio.wait_for(
                            self._mcp.call_tool(
                                "collect_posts",
                                {
                                    "channel_username": channel_username,
                                    "user_id": user_id,
                                    "wait_for_completion": True,
                                    "timeout_seconds": 60,
                                    "hours": hours,
                                    "fallback_to_7_days": fallback_to_7_days,
                                },
                            ),
                            timeout=65.0,  # Slightly longer than tool timeout
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Post collection timeout: user_id={user_id}, "
                            f"channel={channel_username}"
                        )
                        # Subscription succeeded, but collection timed out
                        return SubscribeWithCollectionResult(
                            status=status,
                            channel_username=channel_username,
                            collected_count=0,
                            error="Posts collection timeout - данные собираются в фоне",
                        )

                    collected_count = collect_result.get("collected_count", 0)
                    collect_status = collect_result.get("status", "unknown")

                    # Handle empty results gracefully
                    if collect_status == "success":
                        logger.info(
                            f"Post collection completed: user_id={user_id}, "
                            f"channel={channel_username}, collected={collected_count}"
                        )
                        # Even if 0 posts collected, it's still success
                        # (channel might not have recent posts)
                    elif collect_status == "error":
                        error_type = collect_result.get("error", "unknown")
                        # Handle specific Pyrogram errors
                        if (
                            "pyrogram" in error_type.lower()
                            or "telegram_config" in error_type
                        ):
                            logger.warning(
                                f"Post collection skipped (Pyrogram not available): "
                                f"user_id={user_id}, channel={channel_username}"
                            )
                            # Not a critical error - subscription succeeded
                            return SubscribeWithCollectionResult(
                                status=status,
                                channel_username=channel_username,
                                collected_count=0,
                                error="Posts collection skipped - данные будут собираться автоматически",
                            )
                        else:
                            logger.warning(
                                f"Post collection failed: user_id={user_id}, "
                                f"channel={channel_username}, error={error_type}"
                            )
                            return SubscribeWithCollectionResult(
                                status=status,
                                channel_username=channel_username,
                                collected_count=0,
                                error=f"Posts collection failed: {error_type}",
                            )
                    else:
                        logger.warning(
                            f"Post collection unknown status: user_id={user_id}, "
                            f"channel={channel_username}, status={collect_status}"
                        )
                        return SubscribeWithCollectionResult(
                            status=status,
                            channel_username=channel_username,
                            collected_count=0,
                            error=f"Posts collection status unknown: {collect_status}",
                        )

                    return SubscribeWithCollectionResult(
                        status=status,
                        channel_username=channel_username,
                        collected_count=collected_count,
                    )
                except Exception as collect_error:
                    logger.error(
                        f"Exception during post collection: user_id={user_id}, "
                        f"channel={channel_username}, error={collect_error}",
                        exc_info=True,
                    )
                    # Subscription succeeded, but collection raised exception
                    return SubscribeWithCollectionResult(
                        status=status,
                        channel_username=channel_username,
                        collected_count=0,
                        error=f"Posts collection error: {str(collect_error)}",
                    )

            # Unexpected status
            logger.warning(
                f"Unexpected subscription status: user_id={user_id}, "
                f"channel={channel_username}, status={status}"
            )
            return SubscribeWithCollectionResult(
                status="error",
                channel_username=channel_username,
                collected_count=0,
                error=f"Unexpected subscription status: {status}",
            )

        except Exception as e:
            logger.error(
                f"Exception in subscribe with collection: user_id={user_id}, "
                f"channel={channel_username}, error={e}",
                exc_info=True,
            )
            return SubscribeWithCollectionResult(
                status="error",
                channel_username=channel_username,
                collected_count=0,
                error=f"Subscription error: {str(e)}",
            )
