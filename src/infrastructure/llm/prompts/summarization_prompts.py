"""Improved prompt templates for summarization with quality focus."""

from __future__ import annotations

from typing import Literal


def get_map_prompt(
    text: str, language: Literal["ru", "en"], max_sentences: int = 5
) -> str:
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
        # Load persona style for map phase
        try:
            from src.application.personalization.templates import (
                get_digest_map_prompt,
                get_persona_template,
            )
            persona_template = get_persona_template()
            persona_section = persona_template.format(
                persona="дворецкий",
                tone="witty",
                language="ru",
                preferred_topics="general topics",
            )
            map_template = get_digest_map_prompt()
            return map_template.format(
                persona_section=persona_section,
                max_sentences=max_sentences,
                text=text,
            )
        except Exception:
            # Fallback to old prompt
            pass
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
        f"Summarize the following text fragment from ONE Telegram channel in {max_sentences} sentences.\n\n"
        f"CRITICAL:\n"
        f"- This fragment contains posts from ONLY one channel\n"
        f"- Do NOT mix information from other channels or sources\n"
        f"- Extract facts ONLY from this fragment\n\n"
        f"Requirements:\n"
        f"- Focus on key facts, no repetition, no markdown, NO JSON\n"
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
        f"FRAGMENT (one channel):\n{text}\n\nKEY FACTS:"
    )


def get_reduce_prompt(
    summaries: str, language: Literal["ru", "en"], max_sentences: int = 8
) -> str:
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
        # Load persona style for reduce phase
        try:
            from src.application.personalization.templates import (
                get_digest_reduce_prompt,
                get_persona_template,
            )
            persona_template = get_persona_template()
            persona_section = persona_template.format(
                persona="дворецкий",
                tone="witty",
                language="ru",
                preferred_topics="general topics",
            )
            reduce_template = get_digest_reduce_prompt()
            return reduce_template.format(
                persona_section=persona_section,
                max_sentences=max_sentences,
                summaries=summaries,
            )
        except Exception:
            # Fallback to old prompt
            pass
        return (
            f"Перед тобой несколько суммаризаций фрагментов ОДНОГО Telegram-канала.\n\n"
            f"КРИТИЧЕСКИ ВАЖНО:\n"
            f"- Все эти суммаризации из ОДНОГО канала\n"
            f"- НЕ смешивай информацию из других каналов или источников\n"
            f"- Объединяй ТОЛЬКО информацию из этих суммаризаций\n\n"
            f"ЗАДАЧА: Объедини их в ПОЛНЫЙ, ПОДРОБНЫЙ и ЖИВОЙ дайджест из {max_sentences} итоговых предложений, описывающих главные темы канала. "
            f"Избегай повторов. Каждый пункт — уникальная мысль. Раскрой каждую тему подробно и интересно. Только текст, без нумерации и Markdown.\n\n"
            f"Требования:\n"
            f"- Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные\n"
            f"- НЕ используй фигурные скобки {{}}, квадратные скобки [], кавычки для JSON\n"
            f"- НЕ используй Markdown (* _ ` [ ] ( ))\n"
            f"- Только предложения на русском языке через точку\n"
            f"- НЕ нумеруй предложения (не используй 1., 2., и т.д.)\n"
            f"- Объедини похожие темы, избегай дублирования\n"
            f"- Используй ВСЕ {max_sentences} предложений - пиши подробно и интересно, не обрезай содержание\n"
            f"- Включи все важные детали и аспекты из исходных суммаризаций\n"
            f"- Используй разнообразные формулировки, сделай текст живым и увлекательным\n\n"
            f"ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:\n"
            f"OpenAI представила GPT-4 Turbo с улучшенными возможностями. "
            f"Компания анонсировала интеграцию с Microsoft Azure. "
            f"Разработчики получили доступ к API с расширенными лимитами.\n\n"
            f"ПРИМЕР НЕПРАВИЛЬНОГО ОТВЕТА:\n"
            f"1. OpenAI GPT-4\n"
            f"{{'summary': ['GPT-4', 'Azure integration']}}\n"
            f"*OpenAI* представила **GPT-4**\n\n"
            f"СУММАРИЗАЦИИ ФРАГМЕНТОВ (один канал):\n{summaries}\n\nИТОГОВАЯ СУММАРИЗАЦИЯ:"
        )
    return (
        f"Combine these chunk summaries from ONE Telegram channel into {max_sentences} final sentences covering main topics.\n\n"
        f"CRITICAL:\n"
        f"- All these summaries are from ONE channel\n"
        f"- Do NOT mix information from other channels or sources\n"
        f"- Combine ONLY information from these summaries\n\n"
        f"Requirements:\n"
        f"- No repetition, no markdown, NO JSON\n"
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
        f"CHUNK SUMMARIES (one channel):\n{summaries}\n\nFINAL SUMMARY:"
    )


def get_direct_summarization_prompt(
    text: str,
    language: Literal["ru", "en"],
    max_sentences: int = 8,
    time_period_hours: int | None = None,
    max_chars: int | None = None,
    channel_username: str | None = None,
    channel_title: str | None = None,
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
        channel_username: Optional channel username for context isolation.
        channel_title: Optional channel title for better context.

    Returns:
        Formatted prompt string.
    """
    time_context = ""
    if time_period_hours:
        days = time_period_hours / 24
        if days < 1:
            time_context = (
                f" (за последние {time_period_hours} часов)"
                if language == "ru"
                else f" (last {time_period_hours} hours)"
            )
        elif days == 1:
            time_context = (
                " (за последние 24 часа)" if language == "ru" else " (last 24 hours)"
            )
        elif days < 7:
            time_context = (
                f" (за последние {int(days)} дня)"
                if language == "ru"
                else f" (last {int(days)} days)"
            )
        else:
            time_context = (
                " (за последнюю неделю)" if language == "ru" else " (last week)"
            )

    # Build channel context for better isolation
    channel_context = ""
    if channel_title:
        channel_context = f" канала '{channel_title}'"
    elif channel_username:
        channel_context = f" канала @{channel_username}"

    if language == "ru":
        # Load digest summarization prompt from config (includes persona style)
        try:
            from src.application.personalization.templates import (
                get_digest_summarization_prompt,
                get_persona_template,
            )

            # Get persona section (formatted with default values for digest context)
            persona_template = get_persona_template()
            persona_section = persona_template.format(
                persona="персональный дворецкий",
                tone="witty",
                language="ru",
                preferred_topics="general topics",
            )

            # Get digest prompt template
            digest_template = get_digest_summarization_prompt()

            # Format digest prompt with persona and posts
            return digest_template.format(
                persona_section=persona_section,
                channel_context=channel_context,
                time_context=time_context,
                posts_text=text,
            )
        except Exception as e:
            # Fallback to old prompt if template loading fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Could not load digest prompt from config, using fallback: {e}",
                exc_info=True,
            )
            # Use old prompt as fallback
            return (
                f"Суммаризируй эти посты из Telegram-канала{channel_context}{time_context}.\n\n"
                f"КРИТИЧЕСКИ ВАЖНО:\n"
                f"- Эти посты ВСЕ из ОДНОГО канала{channel_context}\n"
                f"- НЕ смешивай информацию из других каналов или источников\n"
                f"- Суммаризируй ТОЛЬКО то, что написано в этих постах\n\n"
                f"Требования:\n"
                f"- Напиши ПОЛНЫЙ, ПОДРОБНЫЙ и ЖИВОЙ дайджест из {max_sentences} РАЗНЫХ предложений на русском языке\n"
                f"- Каждое предложение раскрывает РАЗНЫЙ аспект или тему\n"
                f"- Без повторов, без нумерации, без Markdown\n"
                f"- Обычный текст, только предложения\n\n"
                f"Формат ответа:\n"
                f"- Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные\n"
                f"- Только предложения на русском языке\n"
                f"- Пиши ПОЛНЫЙ, ДЕТАЛЬНЫЙ и ИНТЕРЕСНЫЙ дайджест - используй ВСЕ {max_sentences} предложений, не обрезай текст\n"
                f"- Включи ВСЕ важные детали из постов, опиши ВСЕ темы и аспекты\n"
                f"- Раскрой каждую тему подробно и интересно, не ограничивайся общими фразами\n"
                f"- Используй разнообразные формулировки, сделай текст живым и увлекательным\n"
                f"- Учитывай временной период: это посты{time_context}, сфокусируйся на актуальном контенте за этот период\n"
                + (
                    f"- Целевой размер примерно {max_chars} символов - используй это пространство для подробного и интересного описания\n"
                    if max_chars
                    else ""
                )
                + "\n"
                f"Пример правильного ответа:\n"
                f"Разработчики представили новую версию iOS с улучшенной производительностью на 30%. "
                f"Добавлены новые функции для работы с жестами и улучшена безопасность. "
                f"Обсуждаются отзывы пользователей о стабильности и совместимости.\n\n"
                f"Посты из канала{channel_context}:\n{text}\n\n"
                f"Суммари (только этот канал):"
            )
    else:
        channel_context_en = (
            f" from channel @{channel_username}" if channel_username else ""
        )
        return (
            f"Summarize these Telegram channel posts{channel_context_en}{time_context}.\n\n"
            f"CRITICAL:\n"
            f"- These posts are ALL from ONE channel{channel_context_en}\n"
            f"- Do NOT mix information from other channels or sources\n"
            f"- Summarize ONLY what is written in these posts\n\n"
            f"Requirements:\n"
            f"- Write a FULL, DETAILED and ENGAGING digest in {max_sentences} sentences\n"
            f"- Each sentence should cover a DIFFERENT aspect or topic\n"
            f"- No repetition, no numbering, no Markdown\n"
            f"- Plain text only, sentences only\n\n"
            f"Format:\n"
            f"- Return ONLY plain text, NO JSON, NO structured data\n"
            f"- Write FULL, DETAILED and INTERESTING digest - use ALL {max_sentences} sentences, don't cut content\n"
            f"- Include ALL important details from posts, cover ALL topics and aspects\n"
            f"- Elaborate on each topic in detail and engagingly, don't use generic phrases\n"
            f"- Use varied phrasing, make the text lively and captivating\n"
            f"- Focus on recent content{time_context}\n"
            + (
                f"- Target size approximately {max_chars} characters - use this space for detailed and interesting description\n"
                if max_chars
                else ""
            )
            + "\n"
            f"Example correct output:\n"
            f"Developers released new iOS version with 30% performance improvement. "
            f"New gesture features added and security enhanced. "
            f"Users discuss stability and compatibility feedback.\n\n"
            f"Posts{channel_context_en}:\n{text}\n\n"
            f"Summary (this channel only):"
        )
