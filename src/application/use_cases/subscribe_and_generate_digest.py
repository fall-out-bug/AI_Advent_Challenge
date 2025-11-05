"""Use case for subscribing to channel and generating digest.

Following Clean Architecture: Application layer orchestrates use cases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from src.application.use_cases.subscribe_with_collection import (
    SubscribeToChannelWithCollectionUseCase,
    SubscribeWithCollectionResult,
)
from src.infrastructure.logging import get_logger

logger = get_logger("use_cases.subscribe_and_generate_digest")


class MCPClientProtocol(Protocol):
    """Protocol for MCP client."""

    async def call_tool(
        self, tool_name: str, arguments: dict
    ) -> dict:
        """Call a tool with arguments."""
        ...


@dataclass
class DigestResult:
    """Result of subscribe and digest operation.
    
    Attributes:
        status: Operation status ("success", "error")
        channel_username: Channel username
        summary: Digest summary text (None if no posts)
        post_count: Number of posts in digest
        collected_count: Number of posts collected
        error: Error message if operation failed
    """
    status: str
    channel_username: str
    summary: Optional[str] = None
    post_count: int = 0
    collected_count: int = 0
    error: Optional[str] = None


class SubscribeAndGenerateDigestUseCase:
    """Use case for subscribing to channel and generating digest.
    
    Purpose:
        Subscribes user to channel, collects posts, then generates digest.
        Composes SubscribeToChannelWithCollectionUseCase and get_channel_digest_by_name.
    
    Attributes:
        mcp_client: MCP client for calling tools
        subscribe_use_case: Use case for subscription with collection
    """

    def __init__(
        self,
        mcp_client: MCPClientProtocol | None = None,
        subscribe_use_case: SubscribeToChannelWithCollectionUseCase | None = None,
    ) -> None:
        """Initialize subscribe and generate digest use case.
        
        Args:
            mcp_client: MCP client instance (required if subscribe_use_case not provided)
            subscribe_use_case: Subscribe use case (creates if None)
        """
        if mcp_client is None and subscribe_use_case is None:
            raise ValueError("Either mcp_client or subscribe_use_case must be provided")
        
        self._mcp = mcp_client
        if subscribe_use_case is None:
            self._subscribe_use_case = SubscribeToChannelWithCollectionUseCase(
                mcp_client=mcp_client
            )
        else:
            self._subscribe_use_case = subscribe_use_case

    async def execute(
        self,
        user_id: int,
        channel_username: str,
        hours: int = 72,
    ) -> DigestResult:
        """Execute subscription and digest generation.
        
        Purpose:
            Subscribe to channel, collect posts, then generate digest.
            Handles empty posts gracefully.
        
        Args:
            user_id: Telegram user ID
            channel_username: Channel username without @
            hours: Hours to look back for posts (default 72)
        
        Returns:
            DigestResult with status, summary, and counts
        """
        channel_username = channel_username.lstrip("@")
        
        try:
            # Step 1: Subscribe and collect posts
            logger.info(
                f"Subscribing and collecting posts: user_id={user_id}, "
                f"channel={channel_username}, hours={hours}"
            )
            subscribe_result = await self._subscribe_use_case.execute(
                user_id=user_id,
                channel_username=channel_username,
                hours=hours,
                fallback_to_7_days=True,
            )
            
            # If subscription failed, return error
            if subscribe_result.status == "error":
                logger.warning(
                    f"Subscription failed: user_id={user_id}, "
                    f"channel={channel_username}, error={subscribe_result.error}"
                )
                return DigestResult(
                    status="error",
                    channel_username=channel_username,
                    error=subscribe_result.error,
                )
            
            # Step 2: Generate digest
            logger.info(
                f"Generating digest: user_id={user_id}, "
                f"channel={channel_username}, hours={hours}"
            )
            digest_result = await self._mcp.call_tool(
                "get_channel_digest_by_name",
                {
                    "user_id": user_id,
                    "channel_username": channel_username,
                    "hours": hours,
                }
            )
            
            digests = digest_result.get("digests", [])
            
            # Handle empty digests (no posts found)
            if not digests:
                message = digest_result.get(
                    "message",
                    f"За последние {hours} часов постов не найдено"
                )
                logger.info(
                    f"No posts found for digest: user_id={user_id}, "
                    f"channel={channel_username}, message={message}"
                )
                return DigestResult(
                    status="success",
                    channel_username=channel_username,
                    summary=message,
                    post_count=0,
                    collected_count=subscribe_result.collected_count,
                )
            
            # Extract first digest (should be only one for single channel)
            first_digest = digests[0]
            summary = first_digest.get("summary", "")
            post_count = first_digest.get("post_count", 0)
            
            logger.info(
                f"Digest generated: user_id={user_id}, "
                f"channel={channel_username}, post_count={post_count}"
            )
            
            return DigestResult(
                status="success",
                channel_username=channel_username,
                summary=summary,
                post_count=post_count,
                collected_count=subscribe_result.collected_count,
            )
            
        except Exception as e:
            logger.error(
                f"Exception in subscribe and generate digest: user_id={user_id}, "
                f"channel={channel_username}, error={e}",
                exc_info=True,
            )
            return DigestResult(
                status="error",
                channel_username=channel_username,
                error=f"Digest generation error: {str(e)}",
            )

