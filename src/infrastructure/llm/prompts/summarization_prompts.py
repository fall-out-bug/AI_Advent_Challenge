"""Improved prompt templates for summarization with quality focus."""

from __future__ import annotations

from typing import Literal


def get_map_prompt(text: str, language: Literal["ru", "en"], max_sentences: int = 5) -> str:
    """Prompt for chunk-level summarization (Map phase).

    Purpose:
        Generate prompt for summarizing a single text chunk.
        Includes strict instructions against JSON and Markdown.

    Args:
        text: Chunk text to summarize.
        language: Target language (ru/en).
        max_sentences: Number of sentences to produce.

    Returns:
        Formatted prompt string.
    """
    if language == "ru":
        return (
            f"Перед тобой фрагмент постов из Telegram-канала.\n\n"
            f"ЗАДАЧА: Выдели {max_sentences} ключевых фактов из этого фрагмента. "
            f"Каждый факт — одно предложение. Факты должны быть РАЗНЫМИ по смыслу. "
            f"Никаких повторов. Только чистый текст, без нумерации и Markdown.\n\n"
            f"КРИТИЧЕСКИ ВАЖНО:\n"
            f"- Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные\n"
            f"- НЕ используй фигурные скобки {{}}, квадратные скобки [], кавычки для JSON\n"
            f"- НЕ используй Markdown (* _ ` [ ] ( ))\n"
            f"- Только предложения на русском языке через точку\n"
            f"- НЕ нумеруй предложения (не используй 1., 2., и т.д.)\n\n"
            f"ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:\n"
            f"OpenAI представила GPT-4 Turbo с контекстным окном 128K. "
            f"Microsoft интегрировал AI в Office 365. Tesla выпустила FSD Beta 11.\n\n"
            f"ПРИМЕР НЕПРАВИЛЬНОГО ОТВЕТА:\n"
            f"1. OpenAI представила GPT-4\n"
            f"{{'summary': 'GPT-4 released'}}\n"
            f"*OpenAI* представила **GPT-4**\n\n"
            f"ФРАГМЕНТ:\n{text}\n\nКЛЮЧЕВЫЕ ФАКТЫ:"
        )
    return (
        f"Summarize the following text fragment in {max_sentences} sentences. "
        f"Focus on key facts, no repetition, no markdown, NO JSON.\n\n"
        f"CRITICAL:\n"
        f"- Return ONLY plain text sentences\n"
        f"- NO JSON, NO structured data (no {{}}, [], quotes for JSON)\n"
        f"- NO Markdown (* _ ` [ ] ( ))\n"
        f"- NO numbering (no 1., 2., etc.)\n\n"
        f"EXAMPLE CORRECT OUTPUT:\n"
        f"OpenAI released GPT-4 Turbo with 128K context window. "
        f"Microsoft integrated AI into Office 365. Tesla launched FSD Beta 11.\n\n"
        f"EXAMPLE WRONG OUTPUT:\n"
        f"1. OpenAI released GPT-4\n"
        f"{{'summary': 'GPT-4 released'}}\n"
        f"*OpenAI* released **GPT-4**\n\n"
        f"FRAGMENT:\n{text}\n\nKEY FACTS:"
    )


def get_reduce_prompt(summaries: str, language: Literal["ru", "en"], max_sentences: int = 8) -> str:
    """Prompt for reduce phase to combine chunk summaries.

    Purpose:
        Generate prompt for combining multiple chunk summaries into final summary.
        Includes strict instructions against JSON and Markdown.

    Args:
        summaries: Combined chunk summaries text.
        language: Target language (ru/en).
        max_sentences: Number of final sentences.

    Returns:
        Formatted prompt string.
    """
    if language == "ru":
        return (
            f"Перед тобой несколько суммаризаций фрагментов одного Telegram-канала.\n\n"
            f"ЗАДАЧА: Объедини их в {max_sentences} итоговых предложений, описывающих главные темы канала. "
            f"Избегай повторов. Каждый пункт — уникальная мысль. Только текст, без нумерации и Markdown.\n\n"
            f"КРИТИЧЕСКИ ВАЖНО:\n"
            f"- Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные\n"
            f"- НЕ используй фигурные скобки {{}}, квадратные скобки [], кавычки для JSON\n"
            f"- НЕ используй Markdown (* _ ` [ ] ( ))\n"
            f"- Только предложения на русском языке через точку\n"
            f"- НЕ нумеруй предложения (не используй 1., 2., и т.д.)\n"
            f"- Объедини похожие темы, избегай дублирования\n\n"
            f"ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:\n"
            f"OpenAI представила GPT-4 Turbo с улучшенными возможностями. "
            f"Компания анонсировала интеграцию с Microsoft Azure. "
            f"Разработчики получили доступ к API с расширенными лимитами.\n\n"
            f"ПРИМЕР НЕПРАВИЛЬНОГО ОТВЕТА:\n"
            f"1. OpenAI GPT-4\n"
            f"{{'summary': ['GPT-4', 'Azure integration']}}\n"
            f"*OpenAI* представила **GPT-4**\n\n"
            f"СУММАРИЗАЦИИ ФРАГМЕНТОВ:\n{summaries}\n\nИТОГОВАЯ СУММАРИЗАЦИЯ:"
        )
    return (
        f"Combine these chunk summaries into {max_sentences} final sentences covering main topics. "
        f"No repetition, no markdown, NO JSON.\n\n"
        f"CRITICAL:\n"
        f"- Return ONLY plain text sentences\n"
        f"- NO JSON, NO structured data (no {{}}, [], quotes for JSON)\n"
        f"- NO Markdown (* _ ` [ ] ( ))\n"
        f"- NO numbering (no 1., 2., etc.)\n"
        f"- Merge similar topics, avoid duplication\n\n"
        f"EXAMPLE CORRECT OUTPUT:\n"
        f"OpenAI released GPT-4 Turbo with improved capabilities. "
        f"The company announced integration with Microsoft Azure. "
        f"Developers gained access to API with expanded limits.\n\n"
        f"EXAMPLE WRONG OUTPUT:\n"
        f"1. OpenAI GPT-4\n"
        f"{{'summary': ['GPT-4', 'Azure integration']}}\n"
        f"*OpenAI* released **GPT-4**\n\n"
        f"CHUNK SUMMARIES:\n{summaries}\n\nFINAL SUMMARY:"
    )


def get_direct_summarization_prompt(
    text: str,
    language: Literal["ru", "en"],
    max_sentences: int = 8,
    time_period_hours: int | None = None,
    max_chars: int | None = None,
) -> str:
    """Prompt for direct summarization (without Map-Reduce).

    Purpose:
        Generate prompt for direct summarization of text.
        Includes contextual metadata and strict quality instructions.

    Args:
        text: Text to summarize.
        language: Target language (ru/en).
        max_sentences: Maximum sentences in summary.
        time_period_hours: Optional time period for context.
        max_chars: Optional maximum characters (soft limit, not hard truncation).

    Returns:
        Formatted prompt string.
    """
    time_context = ""
    if time_period_hours:
        days = time_period_hours / 24
        if days < 1:
            time_context = f" (за последние {time_period_hours} часов)" if language == "ru" else f" (last {time_period_hours} hours)"
        elif days == 1:
            time_context = " (за последние 24 часа)" if language == "ru" else " (last 24 hours)"
        elif days < 7:
            time_context = f" (за последние {int(days)} дня)" if language == "ru" else f" (last {int(days)} days)"
        else:
            time_context = " (за последнюю неделю)" if language == "ru" else " (last week)"

    if language == "ru":
        return (
            f"Суммаризируй эти посты из Telegram-канала{time_context}. "
            f"Напиши {max_sentences} РАЗНЫХ предложения на русском языке. "
            f"Каждое предложение раскрывает РАЗНЫЙ аспект. Без повторов. "
            f"Без нумерации. Без Markdown. Обычный текст.\n\n"
            f"ВАЖНО:\n"
            f"- Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные\n"
            f"- Только предложения на русском языке\n"
            f"- Пиши ПОЛНЫЙ дайджест - не обрезай текст, используй все {max_sentences} предложений\n"
            f"- Включи все важные детали из постов, опиши все темы\n"
            f"- Учитывай временной период: это посты{time_context}, сфокусируйся на актуальном контенте\n"
            + (f"- Старайся уложиться примерно в {max_chars} символов, но не жертвуй важной информацией\n" if max_chars else "") +
            "\n"
            f"Пример правильного ответа:\n"
            f"Разработчики представили новую версию iOS с улучшенной производительностью на 30%. "
            f"Добавлены новые функции для работы с жестами и улучшена безопасность. "
            f"Обсуждаются отзывы пользователей о стабильности и совместимости.\n\n"
            f"Посты:\n{text}\n\nСуммари:"
        )
    return (
        f"Summarize these channel posts{time_context} in {max_sentences} sentence(s). "
        f"Write a full digest with all important details, no Markdown, no JSON. "
        f"Return ONLY plain text sentences.\n\n"
        f"IMPORTANT:\n"
        f"- Return ONLY plain text, NO JSON, NO structured data\n"
        f"- Write FULL digest - use all {max_sentences} sentences, don't cut content\n"
        f"- Include all important details from posts, cover all topics\n"
        f"- Focus on recent content{time_context}\n"
        + (f"- Aim for approximately {max_chars} characters, but don't sacrifice important information\n" if max_chars else "") +
        "\n"
        f"Example correct output:\n"
        f"Developers released new iOS version with 30% performance improvement. "
        f"New gesture features added and security enhanced. "
        f"Users discuss stability and compatibility feedback.\n\n"
        f"Posts:\n{text}\n\nSummary:"
    )
