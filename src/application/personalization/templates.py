"""Prompt templates for personalized interactions.

Templates are loaded from config/persona_templates.yaml for easy editing.
"""

import os
from pathlib import Path
from typing import Dict

import yaml

# Load templates from YAML file
_TEMPLATES_CACHE: Dict[str, str] | None = None


def _load_templates() -> Dict[str, str]:
    """Load persona templates from YAML file.

    Purpose:
        Load templates from config/persona_templates.yaml.
        Caches templates in memory after first load.

    Returns:
        Dictionary with template keys and values.

    Raises:
        FileNotFoundError: If template file doesn't exist.
        yaml.YAMLError: If YAML is invalid.

    Example:
        >>> templates = _load_templates()
        >>> "persona_template" in templates
        True
    """
    global _TEMPLATES_CACHE

    if _TEMPLATES_CACHE is not None:
        return _TEMPLATES_CACHE

    # Find config directory (works from project root or src/)
    project_root = Path(__file__).parent.parent.parent
    template_file = project_root / "config" / "persona_templates.yaml"

    if not template_file.exists():
        # Fallback to default templates if file doesn't exist
        _TEMPLATES_CACHE = _get_default_templates()
        return _TEMPLATES_CACHE

    with open(template_file, "r", encoding="utf-8") as f:
        templates = yaml.safe_load(f)

    _TEMPLATES_CACHE = {
        "persona_template": templates.get("persona_template", ""),
        "memory_context_template": templates.get("memory_context_template", ""),
        "full_prompt_template": templates.get("full_prompt_template", ""),
        "summary_section_template": templates.get("summary_section_template", ""),
        "events_section_template": templates.get("events_section_template", ""),
        "interest_extraction_prompt": templates.get("interest_extraction_prompt", ""),
        "digest_summarization_prompt": templates.get("digest_summarization_prompt", ""),
        "digest_map_prompt": templates.get("digest_map_prompt", ""),
        "digest_reduce_prompt": templates.get("digest_reduce_prompt", ""),
    }

    return _TEMPLATES_CACHE


def _get_default_templates() -> Dict[str, str]:
    """Get default templates as fallback.

    Purpose:
        Provides default templates if YAML file is missing.

    Returns:
        Dictionary with default template values.
    """
    return {
        "persona_template": """Ты — {persona}. Твой тон: {tone}. Язык ответа: {language}.

Instructions:
- Отвечай как Alfred из Batman (вежливый, ироничный, заботливый).
- Используй английский юмор, но говори на русском языке.
- Будь полезным и информативным, но добавляй лёгкую иронию где уместно.
- Preferred topics: {preferred_topics}.
- Обращайся к пользователю на "вы" или "сэр" для поддержания стиля Alfred.

Примеры стиля:
- "Добрый день, сэр. Надеюсь, день проходит без излишней драмы?"
- "Ах, вечный вопрос. Позвольте проверить свои архивы..."
- "Конечно, сэр. Хотя я бы рекомендовал немного больше внимания к деталям в будущем."
""",
        "memory_context_template": """Контекст предыдущих взаимодействий:

{summary_section}
{events_section}
""",
        "full_prompt_template": """{persona_section}

---

{memory_context}

---

User: {new_message}
Butler:""",
        "summary_section_template": """Summary of earlier interactions:
{summary}
""",
        "events_section_template": """Recent conversation:
{events}""",
        "digest_summarization_prompt": """{persona_section}

---

Твоя задача: суммаризировать посты из Telegram-канала{channel_context}{time_context} в стиле дворецкого.

КРИТИЧЕСКИ ВАЖНО:
- Эти посты ВСЕ из ОДНОГО канала{channel_context}
- НЕ смешивай информацию из других каналов или источников
- Суммаризируй ТОЛЬКО то, что написано в этих постах

ТРЕБОВАНИЯ К ДАЙДЖЕСТУ:
- Длина: ровно 1500-2000 символов (включая пробелы)
- Стиль: следуй своему стилю из инструкций выше
- Формат: связный текст, без нумерации, без Markdown, без списков
- Содержание: все важные темы из постов, но кратко и по делу

Посты из канала{channel_context}:
{posts_text}

Дайджест в стиле дворецкого (1500-2000 символов):""",
        "digest_map_prompt": """{persona_section}

---

Ты — дворецкий, готовящий дайджест. Выдели {max_sentences} ключевых фактов из этого фрагмента.

ЗАДАЧА: Каждый факт — одно предложение. Факты должны быть РАЗНЫМИ по смыслу. Никаких повторов. Только чистый текст, без нумерации и Markdown.

ВАЖНО: Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные. Только предложения на русском языке через точку.

ФРАГМЕНТ:
{text}

КЛЮЧЕВЫЕ ФАКТЫ:""",
        "digest_reduce_prompt": """{persona_section}

---

Ты — дворецкий, готовящий финальный дайджест. Объедини суммаризации в {max_sentences} итоговых предложений.

ЗАДАЧА: Описывай главные темы канала. Избегай повторов. Каждый пункт — уникальная мысль. Только текст, без нумерации и Markdown. Длина: 1500-2000 символов.

ВАЖНО: Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные. Только предложения на русском языке через точку.

СУММАРИЗАЦИИ ФРАГМЕНТОВ:
{summaries}

ИТОГОВАЯ СУММАРИЗАЦИЯ (1500-2000 символов):""",
        "interest_extraction_prompt": """Analyze the following conversation history and extract:
1. Summary: Brief summary of what was discussed (max 300 tokens)
2. Interests: List of 3-7 recurring topics, technologies, or domains the user cares about

Rules for interests:
- Focus on technologies (Python, Docker), concepts (RAG, Clean Architecture), domains (ML, Telegram bots)
- Use clear, canonical names (e.g., "Python" not "python coding")
- Exclude sensitive data (API keys, passwords, personal info, file paths)
- Prefer stability: if user mentioned topic before, keep it

Output format (JSON):
{{
  "summary": "User discussed Python development and asked about...",
  "interests": ["Python", "Docker", "Clean Architecture", "Telegram bots"]
}}

Conversation history:
{{events}}

Existing interests: {{existing_topics}}

JSON output:
""",
    }


def _get_template(key: str) -> str:
    """Get template by key.

    Purpose:
        Load and return template from YAML file.

    Args:
        key: Template key (e.g., "persona_template").

    Returns:
        Template string.
    """
    templates = _load_templates()
    return templates.get(key, "")


# Public template accessors (loaded from YAML file)
# Use these functions instead of constants for dynamic loading
def get_persona_template() -> str:
    """Get persona template from YAML file.

    Purpose:
        Load persona template from config/persona_templates.yaml.
        Falls back to defaults if file doesn't exist.

    Returns:
        Persona template string.

    Example:
        >>> template = get_persona_template()
        >>> "Alfred" in template
        True
    """
    return _get_template("persona_template")


def get_memory_context_template() -> str:
    """Get memory context template from YAML file."""
    return _get_template("memory_context_template")


def get_full_prompt_template() -> str:
    """Get full prompt template from YAML file."""
    return _get_template("full_prompt_template")


def get_summary_section_template() -> str:
    """Get summary section template from YAML file."""
    return _get_template("summary_section_template")


def get_events_section_template() -> str:
    """Get events section template from YAML file."""
    return _get_template("events_section_template")


def get_interest_extraction_prompt() -> str:
    """Get interest extraction prompt from YAML file."""
    return _get_template("interest_extraction_prompt")


def get_digest_summarization_prompt() -> str:
    """Get digest summarization prompt from YAML file.
    
    Purpose:
        Load digest summarization prompt template from config/persona_templates.yaml.
        Falls back to defaults if file doesn't exist.
    
    Returns:
        Digest summarization prompt template string.
    """
    return _get_template("digest_summarization_prompt")


def get_digest_map_prompt() -> str:
    """Get digest map phase prompt from YAML file.
    
    Purpose:
        Load map phase prompt template for digest summarization.
    
    Returns:
        Map phase prompt template string.
    """
    return _get_template("digest_map_prompt")


def get_digest_reduce_prompt() -> str:
    """Get digest reduce phase prompt from YAML file.
    
    Purpose:
        Load reduce phase prompt template for digest summarization.
    
    Returns:
        Reduce phase prompt template string.
    """
    return _get_template("digest_reduce_prompt")


# Constants for backward compatibility (loaded from YAML on import)
# These are loaded once at module import time
PERSONA_TEMPLATE = get_persona_template()
MEMORY_CONTEXT_TEMPLATE = get_memory_context_template()
FULL_PROMPT_TEMPLATE = get_full_prompt_template()
SUMMARY_SECTION_TEMPLATE = get_summary_section_template()
EVENTS_SECTION_TEMPLATE = get_events_section_template()


def format_persona_section(
    persona: str, tone: str, language: str, preferred_topics: list[str]
) -> str:
    """Format persona section from profile.

    Purpose:
        Build persona instructions from user profile.

    Args:
        persona: Persona name.
        tone: Conversation tone.
        language: Response language.
        preferred_topics: List of user's preferred topics.

    Returns:
        Formatted persona section.

    Example:
        >>> section = format_persona_section(
        ...     "Alfred-style дворецкий", "witty", "ru", ["Python"]
        ... )
        >>> "Alfred" in section
        True
    """
    topics_str = ", ".join(preferred_topics) if preferred_topics else "general topics"

    template = get_persona_template()
    return template.format(
        persona=persona,
        tone=tone,
        language=language,
        preferred_topics=topics_str,
    )


def format_memory_context(summary: str | None, events: list[str]) -> str:
    """Format memory context from summary and events.

    Purpose:
        Build memory context section for LLM prompt.

    Args:
        summary: Optional summary of older interactions.
        events: List of formatted event strings.

    Returns:
        Formatted memory context.

    Example:
        >>> context = format_memory_context(
        ...     "User likes Python",
        ...     ["- User: Hello", "- Butler: Good day, sir"]
        ... )
        >>> "Summary" in context
        True
    """
    sections = []

    if summary:
        summary_template = get_summary_section_template()
        summary_section = summary_template.format(summary=summary)
        sections.append(summary_section)

    if events:
        events_text = "\n".join(events)
        events_template = get_events_section_template()
        events_section = events_template.format(events=events_text)
        sections.append(events_section)

    if not sections:
        return ""

    memory_template = get_memory_context_template()
    return memory_template.format(
        summary_section=sections[0] if summary else "",
        events_section=(
            sections[1] if len(sections) > 1 else sections[0] if not summary else ""
        ),
    )


def format_full_prompt(
    persona_section: str, memory_context: str, new_message: str
) -> str:
    """Format complete personalized prompt.

    Purpose:
        Assemble all sections into final LLM prompt.

    Args:
        persona_section: Formatted persona instructions.
        memory_context: Formatted memory context.
        new_message: Current user message.

    Returns:
        Complete personalized prompt.

    Example:
        >>> prompt = format_full_prompt("You are Alfred", "Previous: ...", "Hello")
        >>> "Alfred" in prompt and "Hello" in prompt
        True
    """
    full_template = get_full_prompt_template()
    return full_template.format(
        persona_section=persona_section,
        memory_context=memory_context if memory_context else "(No previous context)",
        new_message=new_message,
    )
