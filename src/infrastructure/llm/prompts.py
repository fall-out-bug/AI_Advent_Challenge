"""Prompt templates for Map-Reduce summarization (ru/en) and intent parsing."""

from __future__ import annotations

from typing import Literal


def get_map_prompt(text: str, language: Literal["ru", "en"], max_sentences: int = 5) -> str:
    """Prompt for chunk-level summarization.

    Args:
        text: Chunk text
        language: Target language
        max_sentences: Number of sentences to produce

    Returns:
        Formatted instruction prompt
    """
    if language == "ru":
        return (
            f"Перед тобой фрагмент постов из Telegram-канала.\n\n"
            f"ЗАДАЧА: Выдели {max_sentences} ключевых фактов из этого фрагмента. Каждый факт — одно предложение. "
            f"Факты должны быть РАЗНЫМИ по смыслу. Никаких повторов. Только чистый текст, без нумерации и Markdown.\n\n"
            f"ВАЖНО: Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные. Только предложения на русском языке через точку.\n\n"
            f"ФРАГМЕНТ:\n{text}\n\nКЛЮЧЕВЫЕ ФАКТЫ:"
        )
    return (
        f"Summarize the following text fragment in {max_sentences} concise sentences. "
        f"Focus on key facts, no repetition, no markdown, NO JSON.\n\n"
        f"Return ONLY plain text sentences.\n\nFRAGMENT:\n{text}\n\nKEY FACTS:"
    )


def get_reduce_prompt(summaries: str, language: Literal["ru", "en"], max_sentences: int = 8) -> str:
    """Prompt for reduce phase to combine chunk summaries.

    Args:
        summaries: Combined chunk summaries
        language: Target language
        max_sentences: Number of final sentences

    Returns:
        Formatted instruction prompt
    """
    if language == "ru":
        return (
            f"Перед тобой несколько суммаризаций фрагментов одного Telegram-канала.\n\n"
            f"ЗАДАЧА: Объедини их в {max_sentences} итоговых предложений, описывающих главные темы канала. "
            f"Избегай повторов. Каждый пункт — уникальная мысль. Только текст, без нумерации и Markdown.\n\n"
            f"ВАЖНО: Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные. Только предложения на русском языке через точку.\n\n"
            f"СУММАРИЗАЦИИ ФРАГМЕНТОВ:\n{summaries}\n\nИТОГОВАЯ СУММАРИЗАЦИЯ:"
        )
    return (
        f"Combine these chunk summaries into {max_sentences} final sentences covering main topics. "
        f"No repetition, no markdown, NO JSON.\n\n"
        f"Return ONLY plain text sentences.\n\nCHUNK SUMMARIES:\n{summaries}\n\nFINAL SUMMARY:"
    )


def get_intent_parse_prompt(text: str, language: Literal["ru", "en"] = "en", context: dict | None = None) -> str:
    """Prompt for parsing natural language task intent.

    Args:
        text: User's natural language input
        language: Target language for prompt
        context: Optional conversation context (timezone, user preferences)

    Returns:
        Formatted instruction prompt for intent extraction
    """
    context_str = ""
    if context:
        if "timezone" in context:
            context_str += f"\nКонтекст: часовой пояс {context['timezone']}" if language == "ru" else f"\nContext: timezone {context['timezone']}"
        if "prev_tasks" in context:
            context_str += f"\nПредыдущие задачи: {len(context['prev_tasks'])}" if language == "ru" else f"\nPrevious tasks: {len(context['prev_tasks'])}"

    if language == "ru":
        return (
            f"Извлеки структурированную информацию о задаче из текста пользователя.\n\n"
            f"ТЕКСТ: {text}{context_str}\n\n"
            f"Верни JSON с полями:\n"
            f"- title: краткое название задачи\n"
            f"- description: описание (если есть)\n"
            f"- deadline_iso: ISO дата/время (если указано, иначе null)\n"
            f"- priority: 'low'|'medium'|'high'\n"
            f"- tags: список тегов\n"
            f"- needs_clarification: true если нужны уточнения\n"
            f"- questions: список вопросов для уточнения\n\n"
            f"Примеры:\n"
            f"Вход: 'Купить молоко завтра в 15:00'\n"
            f"Выход: {{'title': 'Купить молоко', 'deadline_iso': '2025-12-02T15:00:00Z', 'priority': 'medium', 'needs_clarification': false}}\n\n"
            f"Вход: 'Напомни позвонить маме'\n"
            f"Выход: {{'title': 'Позвонить маме', 'deadline_iso': null, 'priority': 'medium', 'needs_clarification': true, 'questions': ['Когда нужно позвонить?']}}"
        )
    
    return (
        f"Extract structured task information from user text.\n\n"
        f"TEXT: {text}{context_str}\n\n"
        f"Return JSON with fields:\n"
        f"- title: task title\n"
        f"- description: optional description\n"
        f"- deadline_iso: ISO datetime or null\n"
        f"- priority: 'low'|'medium'|'high'\n"
        f"- tags: list of tags\n"
        f"- needs_clarification: true if clarification needed\n"
        f"- questions: list of clarifying questions\n\n"
        f"Examples:\n"
        f"Input: 'Call mom tomorrow at 3pm'\n"
        f"Output: {{'title': 'Call mom', 'deadline_iso': '2025-12-02T15:00:00Z', 'priority': 'medium', 'needs_clarification': false}}\n\n"
        f"Input: 'Remind me to call mom'\n"
        f"Output: {{'title': 'Call mom', 'deadline_iso': null, 'priority': 'medium', 'needs_clarification': true, 'questions': ['When should I call?']}}"
    )


def get_clarification_prompt(missing_fields: list[str], language: Literal["ru", "en"] = "en") -> str:
    """Generate clarifying questions for missing task fields.

    Args:
        missing_fields: List of missing field names (e.g., ['deadline', 'priority'])
        language: Target language for questions

    Returns:
        Formatted prompt for generating clarification questions
    """
    if language == "ru":
        field_names = {
            "deadline": "срок выполнения",
            "priority": "приоритет",
            "title": "название задачи",
            "description": "описание",
        }
        questions = []
        for field in missing_fields:
            if field == "deadline":
                questions.append("Когда нужно выполнить задачу? (дата и время)")
            elif field == "priority":
                questions.append("Какой приоритет? (низкий, средний, высокий)")
            elif field == "title":
                questions.append("Как назвать задачу?")
            elif field == "description":
                questions.append("Добавьте описание задачи")
            else:
                questions.append(f"Уточните поле: {field}")
        return f"Сгенерируй уточняющие вопросы для полей: {', '.join(missing_fields)}.\n\nВопросы: {', '.join(questions)}"
    
    field_names = {
        "deadline": "deadline",
        "priority": "priority",
        "title": "task title",
        "description": "description",
    }
    questions = []
    for field in missing_fields:
        if field == "deadline":
            questions.append("What is the deadline (date and time)?")
        elif field == "priority":
            questions.append("What is the priority? [low, medium, high]")
        elif field == "title":
            questions.append("What should I name the task?")
        elif field == "description":
            questions.append("Add a description")
        else:
            questions.append(f"Please clarify: {field}")
    return f"Generate clarifying questions for missing fields: {', '.join(missing_fields)}.\n\nQuestions: {', '.join(questions)}"
