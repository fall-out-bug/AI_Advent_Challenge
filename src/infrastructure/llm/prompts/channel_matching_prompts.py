"""Prompts for channel name matching using LLM.

Following Python Zen: Explicit is better than implicit.
"""

from typing import List


def get_channel_matching_prompt(input_name: str, channels_list: List[dict]) -> str:
    """Generate prompt for matching channel name using LLM.

    Purpose:
        Create a prompt that instructs the LLM to find the best matching channel
        from a list of subscribed channels based on user input.

    Args:
        input_name: User input (channel name, title, or username)
        channels_list: List of channel dictionaries with username and title

    Returns:
        Formatted prompt string

    Example:
        >>> channels = [
        ...     {"username": "onaboka", "title": "Набока"},
        ...     {"username": "python_daily", "title": "Python Daily"}
        ... ]
        >>> prompt = get_channel_matching_prompt("Набока", channels)
    """
    # Format channels list for prompt
    channels_text = ""
    for idx, channel in enumerate(channels_list, 1):
        username = channel.get("channel_username") or channel.get("username", "unknown")
        title = channel.get("title", "")
        description = channel.get("description", "")
        desc_text = f", Description: {description}" if description else ""
        channels_text += f"{idx}. Username: @{username}, Title: {title}{desc_text}\n"

    prompt = f"""You are a channel name matcher. Given a user input and a list of subscribed channels,
find the best matching channel.

User input: "{input_name}"

Subscribed channels:
{channels_text}

Instructions:
- Match user input to channel username, title, or description (case-insensitive)
- Handle Cyrillic/Latin variants (e.g., "Набока" matches "onaboka")
- Handle partial matches (e.g., "python" matches "python_daily")
- Consider channel description for better matching accuracy
- Consider common abbreviations and variations
- Return confidence score based on match quality:
  * 0.9-1.0: Exact match or very close variant
  * 0.7-0.9: Clear match with minor variations
  * 0.5-0.7: Partial match or reasonable guess
  * Below 0.5: Weak match, should not be used

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "matched": true/false,
  "channel_username": "username" or null,
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}}

Example response for exact match:
{{
  "matched": true,
  "channel_username": "onaboka",
  "confidence": 0.95,
  "reason": "Exact match: user input 'Набока' matches channel title"
}}

Example response for no match:
{{
  "matched": false,
  "channel_username": null,
  "confidence": 0.0,
  "reason": "No matching channel found in subscriptions"
}}"""

    return prompt


def get_channel_matching_prompt_ru(input_name: str, channels_list: List[dict]) -> str:
    """Generate Russian-language prompt for channel matching.

    Purpose:
        Russian version of channel matching prompt for better localization.

    Args:
        input_name: User input (channel name, title, or username)
        channels_list: List of channel dictionaries with username and title

    Returns:
        Formatted prompt string in Russian
    """
    channels_text = ""
    for idx, channel in enumerate(channels_list, 1):
        username = channel.get("channel_username") or channel.get("username", "unknown")
        title = channel.get("title", "")
        description = channel.get("description", "")
        desc_text = f", Описание: {description}" if description else ""
        channels_text += f"{idx}. Username: @{username}, Название: {title}{desc_text}\n"

    prompt = f"""Ты - помощник для сопоставления названий каналов. Получив пользовательский ввод и список подписанных каналов,
найди наилучшее совпадение.

Ввод пользователя: "{input_name}"

Подписанные каналы:
{channels_text}

Инструкции:
- Сопоставь ввод пользователя с username, названием канала или описанием (без учета регистра)
- Обрабатывай кириллические/латинские варианты (например, "Набока" соответствует "onaboka")
- Обрабатывай частичные совпадения (например, "python" соответствует "python_daily")
- Учитывай описание канала для более точного сопоставления
- Учитывай распространенные сокращения и вариации
- Верни оценку уверенности на основе качества совпадения:
  * 0.9-1.0: Точное совпадение или очень близкий вариант
  * 0.7-0.9: Четкое совпадение с незначительными вариациями
  * 0.5-0.7: Частичное совпадение или разумное предположение
  * Ниже 0.5: Слабое совпадение, не должно использоваться

Верни ТОЛЬКО валидный JSON в этом точном формате (без markdown, без блоков кода):
{{
  "matched": true/false,
  "channel_username": "username" или null,
  "confidence": 0.0-1.0,
  "reason": "краткое объяснение"
}}

Пример ответа для точного совпадения:
{{
  "matched": true,
  "channel_username": "onaboka",
  "confidence": 0.95,
  "reason": "Точное совпадение: ввод 'Набока' соответствует названию канала"
}}

Пример ответа для отсутствия совпадения:
{{
  "matched": false,
  "channel_username": null,
  "confidence": 0.0,
  "reason": "Не найдено совпадающего канала в подписках"
}}"""

    return prompt

