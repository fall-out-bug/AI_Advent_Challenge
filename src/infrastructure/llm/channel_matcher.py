"""LLM-based channel matcher for ambiguous queries.

Purpose:
    Use local LLM to match ambiguous channel queries against cached channels.
    Only uses public channel data (title, username) - no PII.
"""

from __future__ import annotations

import json
import re
from typing import List, Optional

from src.infrastructure.clients.llm_client import HTTPLLMClient
from src.infrastructure.llm.prompts.channel_matching_prompts import (
    get_channel_matching_prompt_ru,
)
from src.infrastructure.logging import get_logger

logger = get_logger("llm_channel_matcher")

# Timeout for LLM calls
LLM_TIMEOUT = 10.0
# Minimum confidence threshold
MIN_CONFIDENCE = 0.5
# Max channels to send to LLM (to avoid token limits)
MAX_CHANNELS_FOR_LLM = 100


class LlmChannelMatcher:
    """Match channels using local LLM.

    Purpose:
        For ambiguous queries, use LLM to rank channels from cache.
        Only processes public channels (title, username) - no private data.
    """

    def __init__(self, llm_url: Optional[str] = None) -> None:
        """Initialize matcher.

        Args:
            llm_url: LLM service URL (defaults to LLM_URL env var)
        """
        self.llm_client = HTTPLLMClient(url=llm_url, timeout=LLM_TIMEOUT)

    async def match_channels(
        self, query: str, channels: List[dict], limit: int = 5
    ) -> List[dict]:
        """Match channels using LLM.

        Purpose:
            Send query and channel list to LLM, get ranked results.

        Args:
            query: User search query
            channels: List of channel dicts with username, title (from cache)
            limit: Maximum results to return

        Returns:
            List of matched channels with LLM-assigned scores

        Example:
            >>> matcher = LlmChannelMatcher()
            >>> channels = [{"username": "bolshiepushki", "title": "Крупнокалиберный Переполох"}]
            >>> results = await matcher.match_channels("крупнокалиберный", channels)
        """
        if not channels:
            logger.debug("No channels provided to LLM matcher")
            return []

        # Limit channels to avoid token limits
        channels_to_process = channels[:MAX_CHANNELS_FOR_LLM]
        if len(channels) > MAX_CHANNELS_FOR_LLM:
            logger.debug(
                f"Limiting channels for LLM: {len(channels)} -> {MAX_CHANNELS_FOR_LLM}"
            )

        try:
            # Generate prompt
            prompt = get_channel_matching_prompt_ru(query, channels_to_process)

            logger.debug(
                f"Calling LLM for channel matching: query='{query}', channels={len(channels_to_process)}"
            )

            # Call LLM
            response = await self.llm_client.generate(
                prompt, temperature=0.2, max_tokens=512
            )

            # Parse JSON response
            result = self._parse_llm_response(response, query, channels_to_process)

            if (
                result
                and result.get("matched")
                and result.get("confidence", 0) >= MIN_CONFIDENCE
            ):
                matched_username = result.get("channel_username")

                # Find matching channel
                matched_channel = None
                for channel in channels_to_process:
                    if channel.get("username") == matched_username:
                        matched_channel = channel
                        break

                if matched_channel:
                    # Return single result with LLM score
                    confidence = result.get("confidence", 0.5)
                    llm_score = int(confidence * 100)  # Convert to 0-100 scale

                    logger.info(
                        f"LLM matched channel: query='{query}', "
                        f"username='{matched_username}', confidence={confidence:.2f}"
                    )

                    return [
                        {
                            "username": matched_channel.get("username"),
                            "title": matched_channel.get("title"),
                            "description": matched_channel.get("description", "") or "",
                            "chat_id": matched_channel.get("chat_id"),
                            "score": llm_score,
                            "llm_confidence": confidence,
                            "llm_reason": result.get("reason", ""),
                        }
                    ]

            logger.debug(
                f"LLM did not find confident match: query='{query}', "
                f"result={result}"
            )
            return []

        except Exception as e:
            logger.error(
                f"Error in LLM channel matching: query='{query}', error={e}",
                exc_info=True,
            )
            return []

    def _parse_llm_response(
        self, response: str, query: str, channels: List[dict]
    ) -> Optional[dict]:
        """Parse LLM JSON response.

        Purpose:
            Extract JSON from LLM response, handling markdown code blocks.

        Args:
            response: LLM response text
            query: Original query (for logging)
            channels: Original channels list (for validation)

        Returns:
            Parsed result dict or None if parsing failed
        """
        try:
            # Remove markdown code blocks if present
            response_clean = response.strip()

            # Try to extract JSON from markdown code blocks
            json_match = re.search(
                r'\{[^{}]*"matched"[^{}]*\}', response_clean, re.DOTALL
            )
            if json_match:
                response_clean = json_match.group(0)

            # Try to find JSON object
            if not response_clean.startswith("{"):
                # Look for first {
                start_idx = response_clean.find("{")
                if start_idx >= 0:
                    response_clean = response_clean[start_idx:]
                else:
                    logger.warning(f"No JSON found in LLM response: {response[:200]}")
                    return None

            # Find matching closing brace
            brace_count = 0
            end_idx = -1
            for i, char in enumerate(response_clean):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

            if end_idx > 0:
                response_clean = response_clean[:end_idx]

            # Parse JSON
            result = json.loads(response_clean)

            # Validate structure
            if not isinstance(result, dict):
                logger.warning(f"LLM response is not a dict: {result}")
                return None

            # Validate required fields
            if "matched" not in result:
                logger.warning(f"LLM response missing 'matched' field: {result}")
                return None

            return result

        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse LLM JSON response: {e}, response='{response[:200]}'"
            )
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}", exc_info=True)
            return None
