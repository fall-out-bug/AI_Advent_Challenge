"""Prompt builder for agent requests.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
"""

from typing import List

from src.domain.agents.schemas import AgentRequest, ToolMetadata


class PromptBuilder:
    """Builder for agent prompts with tool descriptions.
    
    Single responsibility: construct prompts with tool context.
    """

    SYSTEM_PROMPT_TEMPLATE = """Ты — AI помощник для работы с Telegram каналами и генерации дайджестов.

Твои обязанности:
1. Парсить намерение пользователя
2. Использовать доступные инструменты для выполнения задач
3. Обрабатывать результаты и формировать ответ

ВАЖНО: НЕ повторяй промпт или инструкции в ответе. Отвечай ТОЛЬКО на запрос пользователя.

Доступные инструменты:
{tools_prompt}

Правила работы с каналами:
- Если пользователь просит дайджест по конкретному каналу (например, "дайджест по каналу Набоки" или "дайджест по каналу @naboki"):
  ВАЖНО: Используй инструмент get_channel_digest_by_name - он автоматически подпишет пользователя на канал если нужно!
  Формат: {{"tool": "get_channel_digest_by_name", "args": {{"user_id": <user_id>, "channel_username": "naboki", "hours": 72}}}}
  - channel_username должен быть БЕЗ символа @ (например, "naboki" или "onaboka", НЕ "@naboki")
  - Для "за последние 3 дня" используй hours=72
  - Для "за последние N дней" используй hours=N*24
  - Всегда используй user_id из контекста запроса (User ID указан выше)
  
- Если пользователь просит дайджест по всем подпискам (без указания конкретного канала):
  Используй get_channel_digest с параметрами user_id и hours
  
- Если нужно проверить подписки пользователя:
  Используй list_channels с параметром user_id
  
- Если нужно подписаться на канал вручную:
  Используй add_channel с параметрами user_id и channel_username (без @)
  
- Если нужно получить метаданные канала (название, описание, количество подписчиков):
  Используй get_channel_metadata с параметрами channel_username и user_id

Правила:
- Всегда используй инструменты для выполнения задач
- Валидируй параметры перед вызовом инструментов
- Обрабатывай ошибки gracefully
- Возвращай понятные ответы пользователю
- НЕ повторяй промпт или инструкции в ответе

Формат ответа при выборе инструмента:
{{
    "tool": "tool_name",
    "args": {{"param1": "value1", "param2": "value2"}}
}}
"""

    SYSTEM_PROMPT_EN = (
        "You are a helpful Telegram digest assistant. "
        "Use provided tools when needed; prefer tool calls over free text. "
        "Respond to the user in Russian."
    )

    def build_prompt(self, request: AgentRequest, tools: List[ToolMetadata]) -> str:
        """Build prompt with tools description.
        
        Args:
            request: Agent request
            tools: List of available tools
            
        Returns:
            Formatted prompt string
        """
        relevant_tool_names = {
            "add_channel", "list_channels", "delete_channel", "get_channel_digest",
            "get_channel_digest_by_name", "get_channel_metadata", "save_posts_to_db",
            "get_posts_from_db", "summarize_posts", "format_digest_markdown",
            "combine_markdown_sections", "convert_markdown_to_pdf"
        }
        
        filtered_tools = [t for t in tools if t.name in relevant_tool_names]
        tools_prompt = self.build_compact_tools_prompt(filtered_tools if filtered_tools else tools[:10])
        
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(
            tools_prompt=tools_prompt
        )
        
        user_message = self.build_user_message(request)
        
        return f"{system_prompt}\n\n{user_message}\n\nОтвет:"

    def build_compact_tools_prompt(self, tools: List[ToolMetadata]) -> str:
        """Build compact tools prompt with only essential info.
        
        Args:
            tools: List of tools
            
        Returns:
            Compact prompt string
        """
        if not tools:
            return "Нет доступных инструментов."
        
        sections = []
        for tool in tools:
            required = tool.input_schema.get("required", [])
            params = [f"{p}*" for p in required[:3]]
            param_str = ", ".join(params) if params else "no params"
            
            desc = tool.description.split('.')[0] if '.' in tool.description else tool.description[:100]
            
            sections.append(f"- {tool.name}: {desc} ({param_str})")
        
        return "\n".join(sections[:15])

    def build_user_message(self, request: AgentRequest) -> str:
        """Build user message part of prompt.
        
        Args:
            request: Agent request
            
        Returns:
            Formatted user message string
        """
        user_message = f"Пользователь: {request.message}\nUser ID: {request.user_id}"
        if request.context:
            context_str = ", ".join(f"{k}={v}" for k, v in request.context.items())
            user_message += f"\nКонтекст: {context_str}"
        return user_message

