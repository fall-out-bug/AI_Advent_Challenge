"""Data handler for Butler Agent DATA mode.

Handles channel digests and student stats collection.
Following Python Zen: Simple is better than complex.
"""

import logging
import re
from typing import Optional

from src.application.use_cases.collect_data_use_case import CollectDataUseCase
from src.domain.agents.handlers.handler import Handler
from src.domain.agents.state_machine import DialogContext
from src.domain.intent import HybridIntentClassifier, IntentType
from src.domain.interfaces.tool_client import ToolClientProtocol
from src.infrastructure.hw_checker.client import HWCheckerClient

logger = logging.getLogger(__name__)


def _escape_markdown(text: str) -> str:
    """Escape Markdown special characters to prevent parsing errors.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for Telegram Markdown parsing
    """
    if not text:
        return ""
    # Escape special Markdown characters that can break parsing
    text = str(text)
    # Replace characters that have special meaning in Markdown
    text = text.replace("*", "")
    text = text.replace("_", "\\_")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("(", "\\(")
    text = text.replace(")", "\\)")
    text = text.replace("`", "\\`")
    return text


class DataHandler(Handler):
    """Handler for DATA mode - channel digests and stats.

    Uses MCP tools to collect and format data summaries.
    Following SOLID: Single Responsibility Principle.
    """

    def __init__(
        self,
        tool_client: ToolClientProtocol,
        hybrid_classifier: Optional[HybridIntentClassifier] = None,
        hw_checker_client: Optional[HWCheckerClient] = None,
        collect_data_use_case: Optional[CollectDataUseCase] = None,
    ):
        """Initialize data handler.

        Args:
            tool_client: MCP tool client for data collection
            hybrid_classifier: Optional hybrid intent classifier for intent detection and entity extraction
            hw_checker_client: Optional HW Checker API client for homework status queries
        """
        self.tool_client = tool_client
        self.hybrid_classifier = hybrid_classifier
        self.hw_checker_client = hw_checker_client
        self._collect_data_use_case = collect_data_use_case or CollectDataUseCase(
            tool_client=tool_client
        )

    async def handle(self, context: DialogContext, message: str) -> str:
        """Handle data collection request.

        Uses hybrid intent classifier if available, falls back to rule-based parsing.

        Args:
            context: Dialog context with state and data
            message: User message text

        Returns:
            Response text with data summary
        """
        # Use hybrid classifier if available (preferred method)
        if self.hybrid_classifier:
            try:
                intent_result = await self.hybrid_classifier.classify(message)
                logger.debug(
                    f"DataHandler: intent={intent_result.intent.value}, "
                    f"confidence={intent_result.confidence:.2f}, entities={intent_result.entities}"
                )

                # Route based on intent type
                if intent_result.intent == IntentType.DATA_SUBSCRIPTION_REMOVE:
                    channel_name = intent_result.entities.get(
                        "channel_name_hint"
                    ) or intent_result.entities.get("channel_username")
                    if channel_name:
                        return await self._unsubscribe_by_name(context, channel_name)
                    # Fallback to parsing if no entity
                    channel_name = self._parse_channel_name_from_unsubscribe(message)
                    if channel_name:
                        return await self._unsubscribe_by_name(context, channel_name)

                elif intent_result.intent == IntentType.DATA_SUBSCRIPTION_ADD:
                    channel_name = intent_result.entities.get("channel_username")
                    if channel_name:
                        return await self._subscribe_to_channel(context, channel_name)
                    # Fallback to parsing if no entity
                    channel_name = self._parse_channel_name_from_subscribe(message)
                    if channel_name:
                        return await self._subscribe_to_channel(context, channel_name)

                elif intent_result.intent == IntentType.DATA_SUBSCRIPTION_LIST:
                    return await self._list_channels(context)

                elif intent_result.intent == IntentType.DATA_DIGEST:
                    # Extract entities from intent result
                    channel_name = intent_result.entities.get("channel_name")
                    days = intent_result.entities.get("days")

                    # Use extracted entities or fallback to parsing
                    if not channel_name:
                        channel_name = self._parse_channel_name_from_message(message)
                    if not days:
                        days = self._parse_days_from_message(message)

                    hours = days * 24
                    if channel_name:
                        return await self._get_channel_digest_by_name(
                            context, channel_name, hours
                        )
                    else:
                        return await self._get_channels_digest(context, hours=hours)

                elif intent_result.intent == IntentType.DATA_STATS:
                    # Double-check: if message contains homework-related keywords, route to HW status instead
                    message_lower = message.lower()
                    hw_keywords = [
                        "проверок домашних",
                        "проверки домашних",
                        "проверки домашк",
                        "домашних заданий",
                        "домашних работ",
                        "домашек",
                        "homework",
                        "hw",
                        "проверок",
                        "полный статус",
                        "полный статус домашних",
                        "статус домашних",
                        "статус домашних работ",
                    ]
                    # More aggressive matching: check for any homework-related content
                    has_hw = any(
                        keyword in message_lower for keyword in hw_keywords
                    ) or (
                        "статус" in message_lower
                        and ("домашн" in message_lower or "работ" in message_lower)
                    )
                    if has_hw:
                        logger.info(
                            f"Redirecting DATA_STATS to DATA_HW_STATUS based on message content: {message[:100]}"
                        )
                        return await self._get_hw_status(context)
                    return await self._get_student_stats(context)

                elif intent_result.intent == IntentType.DATA_HW_STATUS:
                    return await self._get_hw_status(context)

                elif intent_result.intent == IntentType.DATA_HW_QUEUE:
                    return await self._get_hw_queue_status(context)

                elif intent_result.intent == IntentType.DATA_HW_RETRY:
                    # Extract submission identifier from entities
                    submission_id = intent_result.entities.get("submission_id", {})
                    assignment = intent_result.entities.get("assignment")

                    job_id = (
                        submission_id.get("job_id")
                        if isinstance(submission_id, dict)
                        else None
                    )
                    archive_name = (
                        submission_id.get("archive_name")
                        if isinstance(submission_id, dict)
                        else None
                    )
                    commit_hash = (
                        submission_id.get("commit_hash")
                        if isinstance(submission_id, dict)
                        else None
                    )

                    # Fallback: try to parse from message if entities not extracted
                    if not any([job_id, archive_name, commit_hash]):
                        identifier = self._parse_submission_identifier_from_message(
                            message
                        )
                        if identifier:
                            job_id = identifier.get("job_id")
                            archive_name = identifier.get("archive_name")
                            commit_hash = identifier.get("commit_hash")

                    return await self._retry_hw_submission(
                        context,
                        job_id=job_id,
                        archive_name=archive_name,
                        commit_hash=commit_hash,
                        assignment=assignment,
                    )
            except Exception as e:
                logger.warning(
                    f"Hybrid classifier failed in DataHandler: {e}, falling back to rule-based parsing"
                )

        # Fallback to rule-based parsing (backward compatibility)
        message_lower = message.lower()

        # Check for unsubscribe requests first (more specific)
        unsubscribe_checks = [
            "отпис",
            "отпиш",
            "unsubscribe",
            "удал",
            "remove",
            "убери",
        ]
        if any(check in message_lower for check in unsubscribe_checks):
            channel_name = self._parse_channel_name_from_unsubscribe(message)
            if channel_name:
                return await self._unsubscribe_by_name(context, channel_name)

        # Check for subscription requests (add channel)
        subscribe_keywords = ["подпиш", "subscribe", "добав", "add"]
        if any(keyword in message_lower for keyword in subscribe_keywords):
            channel_name = self._parse_channel_name_from_subscribe(message)
            if channel_name:
                return await self._subscribe_to_channel(context, channel_name)

        # Check for subscription/channel list requests FIRST (before digest)
        list_indicators = [
            "мои подписк",
            "мои каналы",
            "my subscription",
            "my subscriptions",
            "list",
            "список",
            "покажи",
            "show",
            "give me",
            "give me all",
            "all my",
            "все мои",
        ]
        if any(indicator in message_lower for indicator in list_indicators):
            if any(
                word in message_lower
                for word in ["подписк", "subscription", "канал", "channels"]
            ):
                return await self._list_channels(context)

        if (
            "channel" in message_lower
            or "digest" in message_lower
            or "дайджест" in message_lower
        ):
            channel_name = self._parse_channel_name_from_message(message)
            days = self._parse_days_from_message(message)
            hours = days * 24
            if channel_name:
                return await self._get_channel_digest_by_name(
                    context, channel_name, hours
                )
            else:
                return await self._get_channels_digest(context, hours=hours)
        # Check for homework-related keywords FIRST (before student stats)
        # More specific patterns first
        if any(
            keyword in message_lower
            for keyword in [
                "статус проверки домашних",
                "статус проверки домашк",
                "статус домашних заданий",
                "статус домашек",
                "статус домашк",
                "homework status",
                "hw status",
                "проверки домашних",
            ]
        ):
            return await self._get_hw_status(context)
        elif (
            "student" in message_lower
            or (
                "stats" in message_lower
                and "homework" not in message_lower
                and "hw" not in message_lower
            )
            or "статистика" in message_lower
        ):
            return await self._get_student_stats(context)
        elif any(
            keyword in message_lower
            for keyword in ["статус очеред", "queue status", "очередь"]
        ):
            return await self._get_hw_queue_status(context)
        elif any(
            keyword in message_lower
            for keyword in ["перезапусти сабмит", "retry submission", "retry сабмит"]
        ):
            # Try to extract identifier from message
            identifier = self._parse_submission_identifier_from_message(message)
            if identifier:
                job_id = identifier.get("job_id")
                archive_name = identifier.get("archive_name")
                commit_hash = identifier.get("commit_hash")
                return await self._retry_hw_submission(
                    context,
                    job_id=job_id,
                    archive_name=archive_name,
                    commit_hash=commit_hash,
                )
            else:
                return "❌ Не удалось определить идентификатор сабмита. Укажите job_id, archive_name или commit_hash."
        return await self._get_channels_digest(context)

    def _parse_channel_name_from_message(self, message: str) -> str | None:
        """Parse channel name from message.

        Args:
            message: User message text

        Returns:
            Channel username (without @) or None
        """
        # Common stop words to filter out
        stop_words = {
            "за",
            "на",
            "по",
            "дн",
            "дня",
            "дней",
            "день",
            "дней",
            "days",
            "day",
            "of",
            "for",
            "the",
            "a",
            "an",
            "in",
            "at",
            "on",
            "to",
            "from",
            "канала",
            "channel",
            "channels",
            "digest",
            "дайджест",
        }

        # Patterns: "дайджест Набоки", "дайджест канала Набоки", "digest Набоки", "по Набоке"
        # English: "digest of xor", "digest for xor", "xor digest"
        patterns = [
            # Russian patterns (more specific first)
            r"дайджест\s+(?:канала\s+)?по\s+([a-zA-Zа-яА-Я0-9_]+)",
            r"по\s+([a-zA-Zа-яА-Я0-9_]+)\s+за",
            r"дайджест\s+(?:канала\s+)?([a-zA-Zа-яА-Я0-9_]+)",
            r"канала\s+([a-zA-Zа-яА-Я0-9_]+)",
            # English patterns (more specific first)
            r"digest\s+(?:of|for)\s+([a-zA-Zа-яА-Я0-9_]+)",  # "digest of xor" or "digest for xor"
            r"digest\s+(?:channel\s+)?([a-zA-Zа-яА-Я0-9_]+)",  # "digest xor" or "digest channel xor"
            r"([a-zA-Zа-яА-Я0-9_]+)\s+digest",  # "xor digest"
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                channel = match.group(1).strip()
                # Remove @ if present
                channel = channel.lstrip("@")
                # Skip common words and stop words
                if channel and channel.lower() not in stop_words and len(channel) >= 2:
                    # Normalize Russian genitive forms (Набоки → Набока, onaboki → onaboka)
                    if channel.lower().endswith("и") and len(channel) > 2:
                        # Remove last letter and add 'a' if it was Russian genitive
                        if re.search(r"[а-яА-Я]", channel):
                            channel = channel[:-1] + "а"
                    elif channel.lower().endswith("е") and len(channel) > 2:
                        # Prepositional case (Набоке → Набока)
                        if re.search(r"[а-яА-Я]", channel):
                            channel = channel[:-1] + "а"
                    return channel
        return None

    def _parse_days_from_message(self, message: str) -> int:
        """Parse number of days from message.

        Args:
            message: User message text

        Returns:
            Number of days (default: 7)
        """
        message_lower = message.lower()

        # Look for patterns like "за 3 дня", "за неделю", "3 дня", "вчера", etc.
        # English: "for 3 days", "3 days", "for a week", "yesterday"

        # First check for "yesterday" / "вчера" (highest priority - should be checked first)
        if "вчера" in message_lower or "yesterday" in message_lower:
            return 1

        patterns = [
            # Russian patterns
            (r"за\s+(\d+)\s+дн", 1),  # "за 3 дня"
            (r"(\d+)\s+дн", 1),  # "3 дня"
            (r"(\d+)\s+день", 1),  # "3 день"
            (r"неделю|недели", 7),  # "за неделю"
            # English patterns
            (r"for\s+(\d+)\s+days?", 1),  # "for 3 days" or "for 3 day"
            (r"(\d+)\s+days?", 1),  # "3 days" or "3 day"
            (r"for\s+a\s+week", 7),  # "for a week"
            (r"for\s+(\d+)\s+weeks?", 7),  # "for 2 weeks" (multiply by 7)
            (r"(\d+)\s+weeks?", 7),  # "2 weeks" (multiply by 7)
        ]

        for pattern, multiplier in patterns:
            match = re.search(pattern, message_lower)
            if match:
                if multiplier == 1:
                    days = int(match.group(1))
                    # Special handling for weeks - check if pattern captures weeks
                    if "week" in pattern:
                        return days * 7
                    return days
                # For fixed multipliers without capture group (like неделю = 7)
                if multiplier != 1 and not match.groups():
                    return multiplier
                # For patterns with capture groups and multiplier (like weeks)
                if match.groups():
                    value = int(match.group(1))
                    if "week" in pattern:
                        return value * 7
                    return value
                return multiplier
        return 7  # Default to 7 days

    async def _get_channel_digest_by_name(
        self, context: DialogContext, channel_name: str, hours: int
    ) -> str:
        """Get digest for specific channel by name.

        Args:
            context: Dialog context with user_id
            channel_name: Channel username (without @)
            hours: Number of hours to look back

        Returns:
            Formatted channel digest text
        """
        try:
            tool_name = "get_channel_digest_by_name"
            params = {
                "user_id": int(context.user_id),
                "channel_username": channel_name.lstrip("@"),
                "hours": hours,
            }

            logger.info(f"Calling {tool_name} with params: {params}")
            result = await self.tool_client.call_tool(tool_name, params)

            logger.info(
                f"Tool {tool_name} returned: keys={list(result.keys()) if isinstance(result, dict) else type(result)}"
            )

            # Handle not_subscribed status with found_channel (offer to subscribe)
            if result.get("status") == "not_subscribed" and result.get("found_channel"):
                found_channel = result.get("found_channel")
                message = result.get("message", "Подписка не найдена.")
                return (
                    f"{message}\n\n"
                    f"Для получения дайджеста подпишитесь на канал: "
                    f"@{found_channel.get('username')} - {found_channel.get('title', '')}"
                )

            # Handle response format
            if "digests" in result:
                digests = result.get("digests", [])
                logger.info(f"Found {len(digests)} digests in result")
                if digests:
                    formatted = self._format_digests(digests)
                    logger.info(f"Formatted digest length: {len(formatted)} chars")
                    return formatted

            message = result.get("message", "Нет данных")
            logger.info(f"No digests found, message: {message}")
            return f"📊 {message}"

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Failed to get channel digest by name: {error_msg}", exc_info=True
            )

            if (
                "connection" in error_msg.lower()
                or "failed" in error_msg.lower()
                or "http" in error_msg.lower()
            ):
                return "❌ Не удалось подключиться к серверу данных. Убедитесь, что MCP сервер запущен."
            safe_channel_name = _escape_markdown(channel_name)
            safe_error = _escape_markdown(error_msg[:100])
            return f"❌ Ошибка при получении дайджеста канала {safe_channel_name}: {safe_error}"

    async def _get_channels_digest(
        self, context: DialogContext, hours: int = 168
    ) -> str:
        """Get channels digest for all subscribed channels.

        Args:
            context: Dialog context with user_id
            hours: Number of hours to look back (default: 168 = 7 days)

        Returns:
            Formatted channels digest text
        """
        try:
            digest_result = await self._collect_data_use_case.get_channels_digest(
                user_id=int(context.user_id), hours=hours
            )
            if digest_result.error:
                error_msg = digest_result.error
                if any(
                    keyword in error_msg.lower()
                    for keyword in ("connection", "failed", "http")
                ):
                    return (
                        "❌ Не удалось подключиться к серверу данных. "
                        "Убедитесь, что MCP сервер запущен и доступен."
                    )
                return f"❌ {error_msg}"

            digests = digest_result.digests
            if not digests:
                return "📊 Нет доступных дайджестов за указанный период."

            if len(digests) == 1:
                return self._format_single_digest(digests[0])
            return self._format_digests(digests)
        except Exception as e:  # pragma: no cover - defensive
            error_msg = str(e)
            logger.error(
                f"Failed to get channels digest (unexpected error): {error_msg}",
                exc_info=True,
            )
            return "❌ Ошибка при получении дайджеста. Попробуйте позже."

    def _parse_channel_name_from_subscribe(self, message: str) -> str | None:
        """Parse channel name from subscribe message.

        Args:
            message: User message text (e.g., "Подпишись на @xor_journal")

        Returns:
            Channel username (without @) or None
        """
        # Patterns: "подпишись на @xor_journal", "subscribe to xor_journal", "добавь канал xor"
        # More specific patterns first
        patterns = [
            r"подпис[а-я]*\s+на\s+@?([a-zA-Zа-яА-Я0-9_]+)",  # "подпишись на @channel"
            r"subscribe\s+to\s+@?([a-zA-Zа-яА-Я0-9_]+)",  # "subscribe to @channel"
            r"добав[а-я]*\s+канал\s+@?([a-zA-Zа-яА-Я0-9_]+)",  # "добавь канал @channel"
            r"add\s+channel\s+@?([a-zA-Zа-яА-Я0-9_]+)",  # "add channel @channel"
            # Patterns without prepositions (direct)
            r"@([a-zA-Zа-яА-Я0-9_]+)",  # Find @channel anywhere
            r"подпис[а-я]*\s+@?([a-zA-Zа-яА-Я0-9_]{3,})",  # "подпишись @channel"
            r"subscribe\s+@?([a-zA-Zа-яА-Я0-9_]{3,})",  # "subscribe @channel"
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                channel = match.group(1).strip().lstrip("@")
                # Filter out common words
                if (
                    channel
                    and len(channel) >= 3
                    and channel.lower()
                    not in [
                        "на",
                        "to",
                        "канал",
                        "channel",
                        "подпиш",
                        "subscribe",
                        "подпишись",
                        "подписать",
                        "добавь",
                        "add",
                    ]
                ):
                    return channel

        # Final fallback: find @channel pattern anywhere in message
        at_channel_match = re.search(
            r"@([a-zA-Zа-яА-Я0-9_]{3,})", message, re.IGNORECASE
        )
        if at_channel_match:
            return at_channel_match.group(1).strip()

        return None

    async def _subscribe_to_channel(
        self, context: DialogContext, channel_username: str
    ) -> str:
        """Subscribe to a channel.

        Args:
            context: Dialog context with user_id
            channel_username: Channel username (without @)

        Returns:
            Success or error message
        """
        try:
            tool_name = "add_channel"
            params = {
                "user_id": int(context.user_id),
                "channel_username": channel_username.lstrip("@"),
            }

            result = await self.tool_client.call_tool(tool_name, params)

            logger.debug(f"add_channel result: {result}, type: {type(result)}")

            # Handle different response formats
            if isinstance(result, str):
                # Try to parse JSON string
                try:
                    import json

                    result = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    pass

            status = result.get("status", "") if isinstance(result, dict) else ""
            if status in ["subscribed", "already_subscribed"]:
                safe_username = _escape_markdown(channel_username)
                return f"✅ Подписка на канал {safe_username} {'добавлена' if status == 'subscribed' else 'уже существует'}."
            else:
                logger.warning(
                    f"Unexpected status from add_channel: {status}, result: {result}"
                )
                safe_username = _escape_markdown(channel_username)
                safe_status = _escape_markdown(status if status else "неизвестен")
                return f"❌ Не удалось подписаться на канал {safe_username}. Статус: {safe_status}"

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to subscribe to channel: {error_msg}", exc_info=True)

            if "connection" in error_msg.lower() or "failed" in error_msg.lower():
                return "❌ Не удалось подключиться к серверу данных. Убедитесь, что MCP сервер запущен."
            return f"❌ Ошибка при подписке на канал: {error_msg[:100]}"

    def _parse_channel_name_from_unsubscribe(self, message: str) -> str | None:
        """Parse channel name from unsubscribe message.

        Args:
            message: User message text (e.g., "Отпишись от XOR")

        Returns:
            Channel name hint or None
        """
        # Patterns: "отпишись от XOR", "unsubscribe from xor_journal", "удали канал XOR"
        patterns = [
            r"отпиш[а-я]*\s+от\s+([a-zA-Zа-яА-Я0-9_]+)",  # "отпишись от XOR"
            r"unsubscribe\s+from\s+([a-zA-Zа-яА-Я0-9_]+)",  # "unsubscribe from XOR"
            r"удал[а-я]*\s+канал.*?([a-zA-Zа-яА-Я0-9_]+)",  # "удали канал XOR"
            r"remove\s+channel.*?([a-zA-Zа-яА-Я0-9_]+)",  # "remove channel XOR"
            r"убери[а-я]*.*?([a-zA-Zа-яА-Я0-9_]{2,})",  # "убери XOR"
            # Fallback: find any word after unsubscribe keyword
            r"отпиш[а-я]*.*?([a-zA-Zа-яА-Я][a-zA-Zа-яА-Я0-9_]{2,})",  # "отпишись XOR"
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                channel = match.group(1).strip().lstrip("@")
                # Skip common words
                if channel and channel.lower() not in [
                    "от",
                    "from",
                    "канал",
                    "channel",
                ]:
                    return channel
        return None

    async def _unsubscribe_by_name(
        self, context: DialogContext, channel_name_hint: str
    ) -> str:
        """Unsubscribe from channel by name using metadata matching.

        Purpose:
            Allows unsubscribing by channel title or partial name.
            Uses metadata (title, description) to match the hint to actual channel username.

        Args:
            context: Dialog context with user_id
            channel_name_hint: Channel name hint (e.g., "XOR", "Набока")

        Returns:
            Success or error message
        """
        try:
            # Step 1: Get user's subscriptions
            list_result = await self.tool_client.call_tool(
                "list_channels", {"user_id": int(context.user_id)}
            )

            channels = []
            if "channels" in list_result:
                channels = list_result.get("channels", [])
            elif isinstance(list_result, list):
                channels = list_result

            if not channels:
                return "📋 У вас нет активных подписок."

            # Step 2: For each channel, get metadata and match
            matched_channel = None
            matched_channel_id = None
            hint_lower = channel_name_hint.lower()

            for channel in channels:
                channel_username = channel.get("channel_username")
                if not channel_username:
                    continue

                # Step 3: Get channel metadata
                try:
                    metadata = await self.tool_client.call_tool(
                        "get_channel_metadata",
                        {
                            "channel_username": channel_username,
                            "user_id": int(context.user_id),
                        },
                    )

                    # Check if metadata matches the hint
                    title = metadata.get("title", "").lower()
                    description = metadata.get("description", "").lower()
                    username = channel_username.lower()

                    # Match by title, description, or username
                    if (
                        hint_lower in title
                        or hint_lower in description
                        or hint_lower in username
                        or username.startswith(hint_lower)
                    ):
                        matched_channel = channel
                        # Get channel_id: try "id" first (from list_channels), then "_id"
                        matched_channel_id = channel.get("id")
                        if not matched_channel_id and "_id" in channel:
                            matched_channel_id = str(channel["_id"])
                        if not matched_channel_id:
                            # If no ID found, try to get from database
                            logger.warning(
                                f"Channel {channel_username} has no ID field"
                            )
                        break
                except Exception as e:
                    logger.debug(f"Failed to get metadata for {channel_username}: {e}")
                    # Try direct username match if metadata fetch fails
                    if (
                        channel_username.lower().startswith(hint_lower)
                        or hint_lower in channel_username.lower()
                    ):
                        matched_channel = channel
                        matched_channel_id = channel.get("id") or str(
                            channel.get("_id", "")
                        )
                        break

            # Step 4: Delete matched channel
            if matched_channel and matched_channel_id:
                logger.info(
                    f"Attempting to delete channel: {matched_channel_id}, user: {context.user_id}"
                )
                delete_result = await self.tool_client.call_tool(
                    "delete_channel",
                    {"user_id": int(context.user_id), "channel_id": matched_channel_id},
                )

                logger.debug(f"delete_channel result: {delete_result}")

                # Handle different response formats
                if isinstance(delete_result, dict):
                    status = delete_result.get("status", "")
                elif isinstance(delete_result, str):
                    # Try to parse JSON string
                    try:
                        import json

                        delete_result = json.loads(delete_result)
                        status = delete_result.get("status", "")
                    except (json.JSONDecodeError, TypeError):
                        status = ""
                else:
                    status = ""

                if status == "deleted":
                    channel_display = matched_channel.get(
                        "channel_username", channel_name_hint
                    )
                    safe_display = _escape_markdown(channel_display)
                    return f"✅ Отписался от канала {safe_display}."
                else:
                    logger.warning(
                        f"Unexpected delete_channel status: {status}, result: {delete_result}"
                    )
                    safe_status = _escape_markdown(status if status else "неизвестен")
                    return f"❌ Не удалось отписаться от канала. Статус: {safe_status}"
            else:
                safe_hint = _escape_markdown(channel_name_hint)
                return f"❌ Канал '{safe_hint}' не найден в ваших подписках."

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to unsubscribe by name: {error_msg}", exc_info=True)

            if "connection" in error_msg.lower() or "failed" in error_msg.lower():
                return "❌ Не удалось подключиться к серверу данных. Убедитесь, что MCP сервер запущен."
            return f"❌ Ошибка при отписке от канала: {error_msg[:100]}"

    async def _list_channels(self, context: DialogContext) -> str:
        """List user's subscribed channels.

        Args:
            context: Dialog context with user_id

        Returns:
            Formatted list of channels
        """
        try:
            tool_name = "list_channels"
            params = {"user_id": int(context.user_id)}

            result = await self.tool_client.call_tool(tool_name, params)
            logger.info(f"list_channels raw result: {result}")

            # Handle different response formats
            if "channels" in result:
                channels = result.get("channels", [])
            elif isinstance(result, list):
                channels = result
            elif result:
                channels = [result]
            else:
                channels = []

            logger.info(f"Extracted {len(channels)} channels from result")

            if not channels:
                return "📋 У вас нет подписок на каналы. Используйте команду для добавления канала."

            # Format channel list with metadata (username, title)
            lines = [f"📋 *Ваши подписки* ({len(channels)}):\n"]
            for i, channel in enumerate(channels, 1):
                channel_username = channel.get(
                    "channel_username", channel.get("channel", "неизвестный")
                )
                channel_title = channel.get("title", channel.get("channel_title", ""))
                active = channel.get("active", True)
                status = "✅" if active else "⏸"

                logger.info(
                    f"Channel {i}: username={channel_username}, title={channel_title}, has_title={bool(channel_title)}, full_channel={channel}"
                )

                # Format: "username, Title" if title exists, otherwise just username
                # Escape Markdown to prevent parsing errors
                if channel_title:
                    safe_username = _escape_markdown(channel_username)
                    safe_title = _escape_markdown(channel_title)
                    channel_display = f"{safe_username}, {safe_title}"
                else:
                    channel_display = _escape_markdown(channel_username)

                lines.append(f"{status} {i}. {channel_display}")

            formatted = "\n".join(lines)
            logger.info(f"Formatted response: {formatted}")
            return formatted

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to list channels: {error_msg}", exc_info=True)

            if "connection" in error_msg.lower() or "failed" in error_msg.lower():
                return "❌ Не удалось подключиться к серверу данных. Убедитесь, что MCP сервер запущен."
            return f"❌ Ошибка при получении списка каналов: {error_msg[:100]}"

    async def _get_student_stats(self, context: DialogContext) -> str:
        """Get student statistics.

        Args:
            context: Dialog context with user_id

        Returns:
            Formatted student stats text
        """
        try:
            stats_result = await self._collect_data_use_case.get_student_stats(
                teacher_id=context.user_id
            )
            if stats_result.error:
                return f"❌ {stats_result.error}"
            if not stats_result.stats:
                return "📊 No student statistics available."
            return self._format_stats(stats_result.stats)
        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"Failed to get student stats: {e}", exc_info=True)
            return "❌ Failed to retrieve student statistics. Please try again."

    def _format_digests(self, digests: list) -> str:
        """Format channel digests for display.

        Args:
            digests: List of channel digest dictionaries

        Returns:
            Formatted text
        """
        if not digests:
            return "📊 Нет доступных дайджестов."

        lines = []
        for digest in digests:
            channel = digest.get(
                "channel_name", digest.get("channel", "Неизвестный канал")
            )
            summary = digest.get("summary", digest.get("text", "Нет резюме"))

            # Clean summary - remove excessive whitespace but preserve structure
            summary = "\n".join(
                line.strip() for line in summary.split("\n") if line.strip()
            )

            # Build formatted message - Escape channel name and summary to prevent Markdown parsing errors
            safe_channel = _escape_markdown(channel)
            safe_summary = _escape_markdown(summary)
            lines.append(f"📌 *{safe_channel}*")
            lines.append("")
            lines.append(safe_summary)
            lines.append("")

        # Single digest - no header needed
        if len(digests) == 1:
            return "\n".join(lines).strip()

        # Multiple digests - add header
        header = f"📊 *Дайджесты каналов* ({len(digests)})\n\n"
        return header + "\n".join(lines).strip()

    def _format_single_digest(self, digest: dict) -> str:
        """Format single channel digest for display.

        Args:
            digest: Single digest dictionary

        Returns:
            Formatted text
        """
        channel = digest.get("channel_name", digest.get("channel", "Неизвестный канал"))
        summary = digest.get("summary", digest.get("text", "Нет резюме"))

        # Clean summary - preserve paragraph structure
        summary = "\n".join(
            line.strip() for line in summary.split("\n") if line.strip()
        )

        # Telegram message limit is 4096 characters
        # Reserve space for header and formatting (~150 chars)
        max_summary_length = 3946

        if len(summary) > max_summary_length:
            # Try to truncate at paragraph boundary
            truncated = summary[:max_summary_length]
            # Look for last paragraph break
            last_double_newline = truncated.rfind("\n\n")
            if (
                last_double_newline > max_summary_length * 0.7
            ):  # If found within last 30%
                summary = truncated[:last_double_newline].strip()
            else:
                # Try sentence boundary
                last_period = truncated.rfind(".")
                if last_period > max_summary_length * 0.8:
                    summary = truncated[: last_period + 1].strip()
                else:
                    summary = truncated.strip()

            summary += "\n\n_(сообщение обрезано)_"

        # Escape both channel name and summary to prevent Markdown parsing errors
        safe_channel = _escape_markdown(channel)
        safe_summary = _escape_markdown(summary)
        return f"📊 *Дайджест канала {safe_channel}*\n\n{safe_summary}"

    async def _get_hw_status(self, context: DialogContext) -> str:
        """Get homework status for last 24 hours.

        Args:
            context: Dialog context

        Returns:
            Formatted homework status text
        """
        if not self.hw_checker_client:
            return "❌ HW Checker client не настроен. Обратитесь к администратору."

        try:
            # Get full status of all checks (uses all_checks_status endpoint)
            result = await self.hw_checker_client.get_all_checks_status(limit=100)

            checks = result.get("checks", [])
            total_count = result.get("total_count", 0)

            if not checks:
                return "📋 Нет проверок за последние 24 часа."

            # Group by status
            status_counts = {}
            for check in checks:
                status = check.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            # Format response (no Markdown to avoid parsing errors)
            lines = [f"📊 Полный статус домашних работ\n"]
            lines.append(f"Всего проверок: {total_count}\n")

            # Status summary
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "running": "🔄",
                "queued": "⏳",
                "error": "⚠️",
                "timeout": "⏱️",
            }

            lines.append("По статусам:")
            for status, count in sorted(status_counts.items()):
                emoji = status_emoji.get(status, "📌")
                lines.append(f"{emoji} {status}: {count}")

            lines.append("\nПоследние проверки (со всеми полями):")

            # Show last 10 checks with all fields
            for check in checks[:10]:
                # Extract all available fields
                job_id = check.get("job_id", "N/A")
                student_id = check.get("student_id", "Неизвестный")
                assignment = check.get("assignment", "N/A")
                status = check.get("status", "unknown")
                progress = check.get("progress", "")
                created_at = check.get("created_at", "")
                updated_at = check.get("updated_at", "")
                archive_name = check.get("archive_name", "")
                commit_hash = check.get("commit_hash", "")
                error_message = check.get("error_message", "")

                # Escape Markdown characters
                safe_job_id = (
                    str(job_id)
                    .replace("*", "")
                    .replace("_", "")
                    .replace("[", "")
                    .replace("]", "")
                )
                safe_student_id = (
                    str(student_id)
                    .replace("*", "")
                    .replace("_", "")
                    .replace("[", "")
                    .replace("]", "")
                )
                safe_assignment = (
                    str(assignment)
                    .replace("*", "")
                    .replace("_", "")
                    .replace("[", "")
                    .replace("]", "")
                )
                safe_progress = (
                    str(progress)
                    .replace("*", "")
                    .replace("_", "")
                    .replace("[", "")
                    .replace("]", "")
                    if progress
                    else ""
                )
                safe_error = (
                    str(error_message)
                    .replace("*", "")
                    .replace("_", "")
                    .replace("[", "")
                    .replace("]", "")
                    if error_message
                    else ""
                )
                safe_archive = (
                    str(archive_name)
                    .replace("*", "")
                    .replace("_", "")
                    .replace("[", "")
                    .replace("]", "")
                    if archive_name
                    else ""
                )
                safe_commit = (
                    str(commit_hash)
                    .replace("*", "")
                    .replace("_", "")
                    .replace("[", "")
                    .replace("]", "")
                    if commit_hash
                    else ""
                )

                emoji = status_emoji.get(status, "📌")

                # Main line: job_id, student, assignment, status
                lines.append(f"{emoji} {safe_job_id[:20]}")
                lines.append(f"   Студент: {safe_student_id}")
                lines.append(f"   Задание: {safe_assignment}")
                lines.append(f"   Статус: {status}")

                # Additional fields if present
                if safe_archive:
                    lines.append(f"   Архив: {safe_archive}")
                if safe_commit:
                    lines.append(f"   Коммит: {safe_commit}")
                if created_at:
                    lines.append(f"   Создан: {created_at}")
                if updated_at:
                    lines.append(f"   Обновлен: {updated_at}")
                if safe_progress and status in ["running", "queued"]:
                    lines.append(f"   Прогресс: {safe_progress[:80]}")
                if safe_error and status in ["failed", "error"]:
                    lines.append(f"   Ошибка: {safe_error[:80]}")

                lines.append("")  # Empty line between checks

            if total_count > 10:
                lines.append(f"... и еще {total_count - 10} проверок")

            return "\n".join(lines)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to get HW status: {error_msg}", exc_info=True)

            if (
                "connection" in error_msg.lower()
                or "failed" in error_msg.lower()
                or "http" in error_msg.lower()
            ):
                return "❌ Не удалось подключиться к серверу проверки домашних работ. Убедитесь, что HW Checker сервер запущен."
            return f"❌ Ошибка при получении статуса домашних работ: {error_msg[:100]}"

    async def _get_hw_queue_status(self, context: DialogContext) -> str:
        """Get homework queue status.

        Args:
            context: Dialog context

        Returns:
            Formatted queue status text
        """
        if not self.hw_checker_client:
            return "❌ HW Checker client не настроен. Обратитесь к администратору."

        try:
            result = await self.hw_checker_client.get_queue_status()

            total_count = result.get("total_count", 0)
            queued_count = result.get("queued_count", 0)
            running_count = result.get("running_count", 0)
            completed_count = result.get("completed_count", 0)
            failed_count = result.get("failed_count", 0)
            jobs = result.get("jobs", [])

            # Format response (no Markdown to avoid parsing errors)
            lines = [f"📋 Статус очереди проверок\n"]
            lines.append(f"Всего задач: {total_count}\n")
            lines.append("По статусам:")
            lines.append(f"⏳ Ожидает: {queued_count}")
            lines.append(f"🔄 Выполняется: {running_count}")
            lines.append(f"✅ Завершено: {completed_count}")
            lines.append(f"❌ Ошибок: {failed_count}\n")

            if jobs:
                lines.append("Задачи в очереди:")
                for job in jobs[:20]:  # Show up to 20 jobs
                    job_id = (
                        str(job.get("job_id", "N/A"))
                        .replace("*", "")
                        .replace("_", "")
                        .replace("[", "")
                        .replace("]", "")
                    )
                    status = job.get("status", "unknown")
                    student_id = (
                        str(job.get("student_id", "Неизвестный"))
                        .replace("*", "")
                        .replace("_", "")
                        .replace("[", "")
                        .replace("]", "")
                    )
                    assignment = (
                        str(job.get("assignment", "N/A"))
                        .replace("*", "")
                        .replace("_", "")
                        .replace("[", "")
                        .replace("]", "")
                    )
                    progress = (
                        str(job.get("progress", ""))
                        .replace("*", "")
                        .replace("_", "")
                        .replace("[", "")
                        .replace("]", "")
                    )

                    emoji = "⏳" if status == "queued" else "🔄"
                    lines.append(f"{emoji} {job_id[:20]}: {student_id} / {assignment}")
                    if progress:
                        lines.append(f"   └─ {progress[:50]}")

                if len(jobs) > 20:
                    lines.append(f"\n... и еще {len(jobs) - 20} задач")
            else:
                lines.append("\nОчередь пуста.")

            return "\n".join(lines)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to get queue status: {error_msg}", exc_info=True)

            if (
                "connection" in error_msg.lower()
                or "failed" in error_msg.lower()
                or "http" in error_msg.lower()
            ):
                return "❌ Не удалось подключиться к серверу проверки домашних работ. Убедитесь, что HW Checker сервер запущен."
            return f"❌ Ошибка при получении статуса очереди: {error_msg[:100]}"

    async def _retry_hw_submission(
        self,
        context: DialogContext,
        job_id: Optional[str] = None,
        archive_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        assignment: Optional[str] = None,
    ) -> str:
        """Retry homework submission check.

        Args:
            context: Dialog context
            job_id: Optional job ID to retry
            archive_name: Optional archive name to retry
            commit_hash: Optional commit hash to retry
            assignment: Optional assignment filter

        Returns:
            Success or error message
        """
        if not self.hw_checker_client:
            return "❌ HW Checker client не настроен. Обратитесь к администратору."

        if not any([job_id, archive_name, commit_hash]):
            return "❌ Необходимо указать job_id, archive_name или commit_hash для перезапуска."

        try:
            result = await self.hw_checker_client.retry_check(
                job_id=job_id,
                archive_name=archive_name,
                commit_hash=commit_hash,
                assignment=assignment,
            )

            new_job_id = result.get("job_id", "N/A")
            status = result.get("status", "unknown")
            message = result.get("message", "")

            if status == "queued":
                identifier = job_id or archive_name or commit_hash
                return f"✅ Сабмит '{identifier}' поставлен в очередь для перезапуска.\nJob ID: {new_job_id}"
            else:
                return f"⚠️ Статус перезапуска: {status}\n{message}"

        except ValueError as e:
            return f"❌ Ошибка валидации: {str(e)}"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to retry submission: {error_msg}", exc_info=True)

            if (
                "connection" in error_msg.lower()
                or "failed" in error_msg.lower()
                or "http" in error_msg.lower()
            ):
                return "❌ Не удалось подключиться к серверу проверки домашних работ. Убедитесь, что HW Checker сервер запущен."
            return f"❌ Ошибка при перезапуске сабмита: {error_msg[:100]}"

    def _parse_submission_identifier_from_message(self, message: str) -> dict:
        """Parse submission identifier from message (job_id, archive_name, or commit_hash).

        Args:
            message: User message text

        Returns:
            Dictionary with job_id, archive_name, or commit_hash (only one set)
        """
        # Patterns to extract identifier after retry/submission keywords
        patterns = [
            # "перезапусти job_id" или "retry job_id"
            r"(?:перезапусти|retry|restart|rerun)\s+job_id\s+([a-zA-Zа-яА-Я0-9_.-]+)",
            # "перезапусти job_id" (без пробела после job_id)
            r"(?:перезапусти|retry|restart|rerun)\s+job[_-]?id[:\s]+([a-zA-Zа-яА-Я0-9_.-]+)",
            # Просто "перезапусти <identifier>" (прямой job_id или archive name)
            r"(?:перезапусти|retry|restart|rerun)\s+([a-zA-Zа-яА-Я0-9_.-]{4,})$",
            # "перезапусти сабмит <identifier>"
            r"(?:перезапусти|retry|restart|rerun)\s+(?:сабмит|submission)\s+([a-zA-Zа-яА-Я0-9_.-]+)",
            # "перезапусти <identifier> для/for сабмит"
            r"(?:перезапусти|retry|restart|rerun)\s+([a-zA-Zа-яА-Я0-9_.-]+)\s+(?:для|for|сабмит|submission)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                identifier = match.group(1).strip()
                pattern_str = pattern  # Keep pattern for context

                # If pattern explicitly mentions "job_id" or "job-id", prioritize job_id
                is_job_id_explicit = "job" in pattern_str.lower()

                # Check if it's an archive name first (most specific)
                if ".zip" in identifier.lower() or re.search(
                    r"[а-яА-Яa-zA-Z]+_[а-яА-Яa-zA-Z]+_hw\d+", identifier, re.IGNORECASE
                ):
                    return {"archive_name": identifier}

                # If pattern explicitly says "job_id", treat as job_id (even if hex-looking)
                if is_job_id_explicit:
                    return {"job_id": identifier}

                # Check if it's a commit hash (hex only, 7-40 chars, no letters A-F in uppercase suggests commit)
                # But exclude if pattern mentions "job"
                if not is_job_id_explicit and re.match(
                    r"^[a-f0-9]{7,40}$", identifier, re.IGNORECASE
                ):
                    return {"commit_hash": identifier}

                # Check if it's a UUID-like job_id (8+ chars, alphanumeric with dashes/underscores)
                # Exclude pure hex strings (those are likely commit hashes, unless explicitly job_id)
                if re.match(r"^[a-zA-Z0-9_-]{8,}$", identifier):
                    # If contains non-hex letters (A-F uppercase or G-Z), it's likely a job_id
                    if re.search(r"[A-FG-Z]", identifier) or not re.match(
                        r"^[a-f0-9_-]+$", identifier, re.IGNORECASE
                    ):
                        return {"job_id": identifier}
                    # Pure hex but with explicit job_id pattern
                    if is_job_id_explicit:
                        return {"job_id": identifier}

                # For long identifiers without explicit pattern, default to job_id
                if len(identifier) >= 8:
                    return {"job_id": identifier}

                # Default to archive_name if it has underscores (likely name_pattern)
                if "_" in identifier:
                    return {"archive_name": identifier}

        return {}

    def _format_stats(self, stats: dict) -> str:
        """Format student stats for display.

        Args:
            stats: Statistics dictionary

        Returns:
            Formatted text
        """
        lines = ["📊 Student Statistics:\n"]
        for key, value in list(stats.items())[:10]:
            lines.append(f"• {key}: {value}")
        return "\n".join(lines)
