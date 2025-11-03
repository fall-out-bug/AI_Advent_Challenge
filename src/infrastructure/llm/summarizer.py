"""LLM-based summarizer for channel posts."""

from __future__ import annotations

import logging
import asyncio
import re
from typing import List

from src.infrastructure.clients.llm_client import LLMClient, get_llm_client, ResilientLLMClient
from src.infrastructure.config.settings import get_settings
from src.infrastructure.llm.token_counter import TokenCounter
from src.infrastructure.llm.chunker import SemanticChunker, TextChunk
from src.infrastructure.llm.prompts import get_map_prompt, get_reduce_prompt
try:
    from prometheus_client import Counter, Histogram  # type: ignore

    _summarization_duration = Histogram(
        "summarization_duration_seconds",
        "Time spent on summarization phases",
        ["phase"],
    )
    _chunks_processed = Counter(
        "summarizer_chunks_processed_total",
        "Total number of chunks processed",
    )
except Exception:  # pragma: no cover - metrics are optional
    _summarization_duration = None
    _chunks_processed = None

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
    # Remove trailing "читать далее" etc. and trailing ellipsis
    text = re.sub(r'\s*(читать\s+далее|read\s+more|подробнее|\.\.\.)\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[\.…]+\s*$', '', text)
    return text.strip()


async def summarize_posts(posts: List[dict], max_sentences: int = None, llm: LLMClient | None = None, time_period_hours: int = None) -> str:
    """Summarize a list of channel posts using LLM with Russian language support.

    Purpose:
        Generate concise summary from multiple posts in Russian.

    Args:
        posts: List of post dictionaries (with 'text' key)
        max_sentences: Maximum sentences in summary (defaults to settings value)
        llm: LLM client (defaults to ResilientLLMClient with auto-fallback)
        time_period_hours: Time period in hours (for prompt context to ensure uniqueness)

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

    # Clean posts (no limit on count - process all posts from last 24 hours)
    cleaned_posts = []
    for post in posts:  # Process all posts, no limit
        text = post.get("text", "")
        cleaned = _clean_text_for_summary(text)
        if cleaned and len(cleaned) > 20:  # Skip very short posts
            cleaned_posts.append(cleaned[:500])  # Limit to 500 chars per post to avoid token overflow
    
    logger.info(f"Summarizing {len(cleaned_posts)} posts (from {len(posts)} total)")
    if cleaned_posts:
        logger.debug(f"Sample posts (first 3): {cleaned_posts[:3]}")
    
    if not cleaned_posts:
        logger.warning("No suitable posts for summarization")
        return "Нет пригодных постов для саммари."

    texts = "\n".join(f"{i+1}. {text}" for i, text in enumerate(cleaned_posts))
    
    # Russian-language prompt with explicit instructions
    time_context = ""
    if time_period_hours:
        days = time_period_hours / 24
        if days < 1:
            time_context = f" (за последние {time_period_hours} часов)"
        elif days == 1:
            time_context = " (за последние 24 часа)"
        elif days < 7:
            time_context = f" (за последние {int(days)} дня/дней)"
        else:
            time_context = f" (за последнюю неделю)"
    
    if language == "ru":
        prompt = f"""Суммаризируй эти посты из Telegram-канала{time_context}. Напиши {max_sentences} РАЗНЫХ предложения на русском языке. Каждое предложение раскрывает РАЗНЫЙ аспект. Без повторов. Без нумерации. Без Markdown. Обычный текст.

ВАЖНО: 
- Верни ТОЛЬКО текст, НЕ JSON, НЕ структурированные данные
- Только предложения на русском языке
- Пиши ПОЛНЫЙ дайджест - не обрезай текст, используй все {max_sentences} предложений
- Включи все важные детали из постов
- Учитывай временной период: это посты{time_context}, сфокусируйся на актуальном контенте за этот период

Пример:
"Разработчики представили новую версию iOS с улучшенной производительностью на 30%. Добавлены новые функции для работы с жестами и улучшена безопасность. Обсуждаются отзывы пользователей о стабильности и совместимости."

Посты:
{texts}

Суммари:"""
    else:
        prompt = f"""Summarize these channel posts in {max_sentences} sentence(s), be very concise, no Markdown, no JSON. Return ONLY plain text sentences.

Posts:
{texts}

Summary:"""

    # If the concatenated cleaned text is long, use Map-Reduce
    full_text = "\n\n".join(cleaned_posts)
    try:
        counter = TokenCounter()
        # Fallback to direct summarization when under threshold
        if counter.count_tokens(full_text) > 3000:
            # Map-Reduce path
            summarizer = MapReduceSummarizer(llm=llm_client, token_counter=counter, language=language)
            return await summarizer.summarize_text(full_text, max_sentences=max_sentences)
    except Exception as e:
        # If token counting fails for any reason (e.g., transformers not available), proceed with direct summarization
        logger.debug(f"TokenCounter unavailable or failed, using direct summarization: {e}")
        pass

    # Generate summary with retry (direct path)
    logger.info(f"Starting summarization with LLM (posts={len(cleaned_posts)}, max_sentences={max_sentences}, temperature={temperature})")
    logger.info(f"Posts content hash (first 3 texts): {hash(str(cleaned_posts[:3]))}")
    logger.debug(f"Prompt (first 500 chars): {prompt[:500]}")
    
    for attempt in range(2):
        try:
            summary = await llm_client.generate(prompt, temperature=temperature, max_tokens=max_tokens)
            logger.info(f"LLM response received (attempt {attempt + 1}, length={len(summary) if summary else 0})")
            if summary:
                logger.debug(f"Raw LLM response (first 300 chars): {summary[:300]}")
            if summary and len(summary.strip()) > 10:
                # Clean summary - remove any remaining Markdown or artifacts
                cleaned_summary = summary.strip()
                
                # If summary is JSON, try to extract text content
                if cleaned_summary.startswith('{') or cleaned_summary.startswith('['):
                    logger.warning("LLM returned JSON instead of text, attempting to extract text: %s", cleaned_summary[:100])
                    # Use same cleaning logic as MapReduceSummarizer
                    cleaned_summary = _clean_json_from_summary(cleaned_summary)
                    # If cleaning failed or result is too short, use fallback
                    if len(cleaned_summary) < 10:
                        logger.warning("JSON cleaning resulted in too short text, raising error to trigger fallback")
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
                    logger.info(f"Final summary generated: {cleaned_summary[:200]}...")
                    return cleaned_summary
        except Exception as e:
            logger.warning("Summarization attempt %d failed: %s", attempt + 1, str(e), exc_info=True)
            if attempt == 1:
                break

    # Fallback to bullet list (Russian) - show all posts, limit only if too long
    logger.warning("Using fallback summarization (LLM failed or returned invalid format)")
    # Don't truncate individual posts - let data_handler handle length limits
    if language == "ru":
        fallback_summary = ". ".join(post.get('text', '').strip() for post in posts if post.get('text', '').strip())
        # Only add truncation marker if really needed
        if len(fallback_summary) > 4000:
            fallback_summary = fallback_summary[:3900] + "..."
    else:
        fallback_summary = "\n".join(f"• {post.get('text', '').strip()}" for post in posts if post.get('text', '').strip())
    logger.debug(f"Fallback summary: {fallback_summary[:200]}...")
    return fallback_summary


def _clean_json_from_summary(summary: str) -> str:
    """Remove JSON artifacts from summary text.
    
    Args:
        summary: Raw summary text that may contain JSON
        
    Returns:
        Cleaned summary text without JSON
    """
    if not summary:
        return ""
    
    cleaned = summary.strip()
    
    # If summary starts with JSON, try to extract text content
    if cleaned.startswith('{') or cleaned.startswith('['):
        logger.warning("LLM returned JSON in summarization, attempting to extract text")
        # Try to extract text from JSON-like structures
        import json
        try:
            # Try to parse as JSON and extract useful fields
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                # Look for 'summary', 'text', 'content', or 'response' fields
                for key in ['summary', 'text', 'content', 'response', 'message']:
                    if key in parsed and isinstance(parsed[key], str):
                        cleaned = parsed[key]
                        break
                # If no text field found, try to concatenate string values
                if cleaned.startswith('{'):
                    text_parts = [str(v) for v in parsed.values() if isinstance(v, str)]
                    if text_parts:
                        cleaned = ' '.join(text_parts)
            elif isinstance(parsed, list):
                # If it's a list, try to join string elements
                text_parts = [str(item) for item in parsed if isinstance(item, str)]
                if text_parts:
                    cleaned = ' '.join(text_parts)
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, just remove JSON-like structures
            pass
    
    # Remove JSON objects and arrays using regex
    cleaned = re.sub(r'\{[^{}]*\}', '', cleaned)  # Remove JSON objects (simple)
    cleaned = re.sub(r'\[[^\[\]]*\]', '', cleaned)  # Remove JSON arrays (simple)
    
    # Remove JSON-like field patterns: "key": "value"
    cleaned = re.sub(r'["\']?\w+["\']?\s*:\s*["\']?([^"\']+)["\']?', r'\1', cleaned)
    
    # Remove common JSON artifacts
    cleaned = cleaned.replace('{', '').replace('}', '').replace('[', '').replace(']', '')
    cleaned = re.sub(r'["\']', '', cleaned)  # Remove quotes
    
    # Clean up whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # If cleaned text is too short or empty, log warning
    if len(cleaned) < 10:
        logger.warning(f"JSON cleaning resulted in very short text: {cleaned[:50]}")
        # Return original if cleaning removed too much
        return summary.strip()
    
    return cleaned


class MapReduceSummarizer:
    """Map-Reduce summarization for long texts."""

    def __init__(
        self,
        llm: LLMClient,
        token_counter: TokenCounter | None = None,
        chunker: SemanticChunker | None = None,
        language: str = "ru",
    ) -> None:
        self.llm = llm
        self.token_counter = token_counter or TokenCounter()
        self.chunker = chunker or SemanticChunker(self.token_counter, max_tokens=3000, overlap_tokens=200)
        self.language = language

    async def _summarize_chunk(self, chunk: TextChunk, max_sentences: int, temperature: float, max_tokens: int) -> str:
        prompt = get_map_prompt(text=chunk.text, language=self.language, max_sentences=max_sentences)
        if _summarization_duration is None:
            summary = await self.llm.generate(prompt, temperature=temperature, max_tokens=max_tokens)
        else:
            with _summarization_duration.labels("map").time():
                summary = await self.llm.generate(prompt, temperature=temperature, max_tokens=max_tokens)
        
        # Clean JSON artifacts from map phase response
        return _clean_json_from_summary(summary)

    async def summarize_text(
        self,
        text: str,
        max_sentences: int = 8,
        temperature: float = 0.2,
        map_max_tokens: int = 600,
        reduce_max_tokens: int = 2000,
    ) -> str:
        chunks = self.chunker.chunk_text(text)
        if len(chunks) == 1:
            return await self._summarize_chunk(chunks[0], max_sentences=max_sentences, temperature=temperature, max_tokens=reduce_max_tokens)

        # Map phase
        if _chunks_processed is not None:
            _chunks_processed.inc(len(chunks))
        summaries = await asyncio.gather(
            *[
                self._summarize_chunk(c, max_sentences=max(3, max_sentences // 2), temperature=temperature, max_tokens=map_max_tokens)
                for c in chunks
            ]
        )

        # Reduce phase
        combined = "\n\n".join([f"Fragment {i+1}:\n{s}" for i, s in enumerate(summaries)])
        prompt = get_reduce_prompt(summaries=combined, language=self.language, max_sentences=max_sentences)
        if _summarization_duration is None:
            final_summary = await self.llm.generate(prompt, temperature=temperature, max_tokens=reduce_max_tokens)
        else:
            with _summarization_duration.labels("reduce").time():
                final_summary = await self.llm.generate(prompt, temperature=temperature, max_tokens=reduce_max_tokens)
        
        # Clean JSON artifacts from reduce phase response
        return _clean_json_from_summary(final_summary)

