"""LLM-based summarizer for channel posts."""

from __future__ import annotations

import logging
import re
from typing import List

from src.infrastructure.clients.llm_client import LLMClient, get_llm_client, ResilientLLMClient
from src.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


def _clean_text_for_summary(text: str) -> str:
    """Clean text for summarization - remove URLs, extra whitespace, etc.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # Remove UTM parameters references
    text = re.sub(r'utm_[a-z_]+', '', text, flags=re.IGNORECASE)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove trailing "читать далее" etc.
    text = re.sub(r'\s*(читать\s+далее|read\s+more|подробнее|\.\.\.)\s*$', '', text, flags=re.IGNORECASE)
    return text.strip()


async def summarize_posts(posts: List[dict], max_sentences: int = None, llm: LLMClient | None = None) -> str:
    """Summarize a list of channel posts using LLM with Russian language support.

    Purpose:
        Generate concise summary from multiple posts in Russian.

    Args:
        posts: List of post dictionaries (with 'text' key)
        max_sentences: Maximum sentences in summary (defaults to settings value)
        llm: LLM client (defaults to ResilientLLMClient with auto-fallback)

    Returns:
        Summary text (or fallback bullet list on failure)
    """
    if not posts:
        return "Нет постов для саммари."

    settings = get_settings()
    max_sentences = max_sentences or settings.digest_summary_sentences
    language = settings.summarizer_language
    temperature = settings.summarizer_temperature
    max_tokens = settings.summarizer_max_tokens

    # Use resilient client if none provided
    if llm is None:
        llm = ResilientLLMClient()
    llm_client = llm

    # Clean and limit posts
    cleaned_posts = []
    for post in posts[:10]:  # Limit to 10 posts
        text = post.get("text", "")
        cleaned = _clean_text_for_summary(text)
        if cleaned and len(cleaned) > 20:  # Skip very short posts
            cleaned_posts.append(cleaned[:150])  # 150 chars per post
    
    if not cleaned_posts:
        return "Нет пригодных постов для саммари."

    texts = "\n".join(f"{i+1}. {text}" for i, text in enumerate(cleaned_posts))
    
    # Russian-language prompt with explicit instructions
    if language == "ru":
        prompt = f"""Суммаризируй эти посты из Telegram-канала. Напиши {max_sentences} РАЗНЫХ предложения на русском языке. Каждое предложение раскрывает РАЗНЫЙ аспект. Без повторов. Без нумерации. Без Markdown. Обычный текст.

Пример:
"Разработчики представили новую версию iOS с улучшенной производительностью на 30%. Добавлены новые функции для работы с жестами и улучшена безопасность. Обсуждаются отзывы пользователей о стабильности и совместимости."

Посты:
{texts}

Суммари:"""
    else:
        prompt = f"""Summarize these channel posts in {max_sentences} sentence(s), be very concise, no Markdown:\n\n{texts}"""

    # Generate summary with retry
    for attempt in range(2):
        try:
            summary = await llm_client.generate(prompt, temperature=temperature, max_tokens=max_tokens)
            if summary and len(summary.strip()) > 10:
                # Clean summary - remove any remaining Markdown or artifacts
                cleaned_summary = summary.strip()
                
                # CRITICAL: If summary is JSON, discard it and use fallback
                if cleaned_summary.startswith('{') or cleaned_summary.startswith('['):
                    logger.warning("LLM returned JSON instead of text, discarding", summary_preview=cleaned_summary[:100])
                    raise ValueError("LLM returned JSON instead of text summary")
                
                # Remove any stray JSON artifacts
                cleaned_summary = re.sub(r'\{[^}]*\}', '', cleaned_summary)  # Remove any JSON objects
                cleaned_summary = re.sub(r'\[[^\]]*\]', '', cleaned_summary)  # Remove any JSON arrays
                
                # Remove numbering patterns (1., 2., First post, Second post, etc.)
                cleaned_summary = re.sub(r'^\d+\.\s*', '', cleaned_summary, flags=re.MULTILINE)
                cleaned_summary = re.sub(r'^(In the )?(first|second|third|fourth|fifth|First|Second|Third)\s+post', '', cleaned_summary, flags=re.IGNORECASE | re.MULTILINE)
                cleaned_summary = re.sub(r'^The (first|second|third|fourth|fifth)\s+post', '', cleaned_summary, flags=re.IGNORECASE | re.MULTILINE)
                
                # If summary is empty or too short after cleaning, use raw text
                if len(cleaned_summary) < 20:
                    logger.warning("Summary too short after cleaning, using raw LLM output")
                    cleaned_summary = summary.strip()
                    # Basic cleanup only
                    cleaned_summary = re.sub(r'[*_`\[\]()]', '', cleaned_summary)
                    cleaned_summary = re.sub(r'\s+', ' ', cleaned_summary).strip()
                
                # If summary contains multiple sentences split by newlines, take only first
                lines = cleaned_summary.split('\n')
                cleaned_summary = lines[0] if lines else cleaned_summary
                
                # Remove common Markdown artifacts
                cleaned_summary = re.sub(r'[*_`\[\]()]', '', cleaned_summary)
                # Remove bullet points
                cleaned_summary = re.sub(r'^[•\-\*]\s*', '', cleaned_summary, flags=re.MULTILINE)
                # Normalize quotes (smart quotes to regular)
                cleaned_summary = cleaned_summary.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
                # Remove extra whitespace
                cleaned_summary = re.sub(r'\s+', ' ', cleaned_summary).strip()
                
                # Final validation: ensure we have max_sentences sentences
                sentences = re.split(r'[.!?]+', cleaned_summary)
                sentences = [s.strip() for s in sentences if s.strip()]
                # Remove duplicate or very similar sentences
                unique_sentences = []
                for sent in sentences:
                    is_duplicate = False
                    for existing in unique_sentences:
                        # Check if sentences are too similar (simple word overlap check)
                        words_sent = set(sent.lower().split())
                        words_existing = set(existing.lower().split())
                        overlap = len(words_sent & words_existing) / max(len(words_sent), len(words_existing)) if words_sent or words_existing else 0
                        if overlap > 0.6:  # More than 60% word overlap
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        unique_sentences.append(sent)
                
                # Use unique sentences, limit to max_sentences
                if len(unique_sentences) > max_sentences:
                    cleaned_summary = '. '.join(unique_sentences[:max_sentences])
                    if not cleaned_summary.endswith(('.', '!', '?')):
                        cleaned_summary += '.'
                elif len(unique_sentences) > 0:
                    cleaned_summary = '. '.join(unique_sentences)
                    if not cleaned_summary.endswith(('.', '!', '?')):
                        cleaned_summary += '.'
                else:
                    # Fallback to original if dedup removed everything
                    cleaned_summary = '. '.join(sentences[:max_sentences]) if sentences else cleaned_summary
                
                if cleaned_summary:
                    return cleaned_summary
        except Exception as e:
            logger.warning(f"Summarization attempt {attempt + 1} failed", error=str(e))
            if attempt == 1:
                break

    # Fallback to bullet list (Russian)
    if language == "ru":
        return ". ".join(f"{post.get('text', '')[:100]}" for post in posts[:3]) + "..."
    else:
        return "\n".join(f"• {post.get('text', '')[:100]}" for post in posts[:5])

