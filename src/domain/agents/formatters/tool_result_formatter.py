"""Tool result formatter for converting tool outputs to user messages.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import json
from typing import Any, Dict


class ToolResultFormatter:
    """Formatter for MCP tool execution results.
    
    Single responsibility: convert tool results into user-friendly text.
    """

    def format(self, result: Dict[str, Any], tool_name: str) -> str:
        """Format tool result for user.
        
        Args:
            result: Tool execution result dictionary
            tool_name: Name of the tool that produced the result
            
        Returns:
            Formatted text message for user
        """
        formatters = {
            "list_channels": self._format_list_channels,
            "add_channel": self._format_add_channel,
            "get_channel_digest": self._format_channel_digest,
            "get_channel_digest_by_name": self._format_channel_digest_by_name,
            "get_channel_metadata": self._format_channel_metadata,
        }
        
        formatter = formatters.get(tool_name)
        if formatter:
            return formatter(result)
        
        return self._format_default_result(result, tool_name)
    
    def _format_list_channels(self, result: Dict[str, Any]) -> str:
        """Format list_channels result.
        
        Args:
            result: Result dictionary with channels list
            
        Returns:
            Formatted message about subscribed channels
        """
        channels = result.get("channels", [])
        if not channels:
            return "У вас пока нет подписок на каналы. Используйте add_channel чтобы подписаться."
        channel_names = [ch.get("channel_username", "unknown") for ch in channels]
        return f"Ваши подписки на каналы ({len(channels)}): {', '.join(channel_names)}"
    
    def _format_add_channel(self, result: Dict[str, Any]) -> str:
        """Format add_channel result.
        
        Args:
            result: Result dictionary with subscription status
            
        Returns:
            Formatted message about subscription status
        """
        status = result.get("status", "")
        if status == "already_subscribed":
            return "Вы уже подписаны на этот канал."
        elif status == "subscribed":
            return "Вы успешно подписались на канал. Теперь можно получить дайджест."
        return f"Результат: {status}"
    
    def _format_channel_digest(self, result: Dict[str, Any]) -> str:
        """Format get_channel_digest result.
        
        Args:
            result: Result dictionary with digests list
            
        Returns:
            Formatted message with channel digests
        """
        digests = result.get("digests", [])
        if not digests:
            return "За указанный период новых постов не найдено."
        return self._format_digest_list(digests)
    
    def _format_channel_digest_by_name(self, result: Dict[str, Any]) -> str:
        """Format get_channel_digest_by_name result.
        
        Args:
            result: Result dictionary with digests and channel info
            
        Returns:
            Formatted message with channel digest
        """
        digests = result.get("digests", [])
        channel = result.get("channel", "Unknown")
        if not digests:
            message = result.get("message", f"За указанный период постов из канала {channel} не найдено.")
            return message
        return self._format_digest_list(digests, default_channel=channel)
    
    def _format_digest_list(self, digests: list, default_channel: str = "") -> str:
        """Format list of digests.
        
        Args:
            digests: List of digest dictionaries
            default_channel: Default channel name if not in digest
            
        Returns:
            Formatted multi-channel digest message
        """
        formatted = []
        for digest in digests:
            channel = digest.get("channel", default_channel or "Unknown")
            summary = digest.get("summary", "")
            post_count = digest.get("post_count", 0)
            formatted.append(f"📌 {channel} ({post_count} постов):\n{summary}")
        return "\n\n".join(formatted)
    
    def _format_channel_metadata(self, result: Dict[str, Any]) -> str:
        """Format get_channel_metadata result.
        
        Args:
            result: Result dictionary with channel metadata or error
            
        Returns:
            Formatted message with channel metadata or error
        """
        if result.get("success"):
            return self._format_metadata_success(result)
        error = result.get("error", "Unknown error")
        message = result.get("message", f"Не удалось получить метаданные канала: {error}")
        return message
    
    def _format_metadata_success(self, result: Dict[str, Any]) -> str:
        """Format successful metadata result.
        
        Args:
            result: Result dictionary with channel metadata
            
        Returns:
            Formatted message with channel information
        """
        title = result.get("title", "Unknown")
        description = result.get("description", "")
        member_count = result.get("member_count", "")
        username = result.get("username", result.get("channel_username", ""))
        formatted = [f"📢 Канал: {title}"]
        if username:
            formatted.append(f"Username: @{username}")
        if description:
            formatted.append(f"Описание: {description}")
        if member_count:
            formatted.append(f"Подписчиков: {member_count:,}")
        return "\n".join(formatted)
    
    def _format_default_result(self, result: Dict[str, Any], tool_name: str) -> str:
        """Format default result for unknown tools.
        
        Args:
            result: Result dictionary from tool execution
            tool_name: Name of the tool
            
        Returns:
            Formatted message or error description
        """
        if result.get("status") == "success":
            data = result.get("data", result.get("result", ""))
            if isinstance(data, str):
                return data
            elif isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return str(data)
        error = result.get("error", "Unknown error")
        return f"Ошибка при выполнении {tool_name}: {error}"

