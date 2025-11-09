"""Prompt templates for LLM-based quality evaluation."""

from __future__ import annotations

from typing import Literal


def get_evaluation_prompt(
    original_text: str,
    summary_text: str,
    language: Literal["ru", "en"] = "ru",
) -> str:
    """Prompt for evaluating summary quality using LLM as judge.

    Purpose:
        Generate prompt for LLM to evaluate summary quality based on
        5 criteria: coverage, accuracy, coherence, informativeness, and overall score.

    Args:
        original_text: Original source text that was summarized.
        summary_text: Generated summary text to evaluate.
        language: Target language for prompt ("ru" | "en").

    Returns:
        Formatted prompt string with evaluation instructions.

    Example:
        >>> prompt = get_evaluation_prompt(
        ...     original_text="Long article...",
        ...     summary_text="Brief summary...",
        ...     language="ru",
        ... )
        >>> # Send prompt to LLM for evaluation
    """
    if language == "ru":
        return f"""Оцени качество суммаризации по 5 критериям (оценка от 0.0 до 1.0):

ОРИГИНАЛЬНЫЙ ТЕКСТ:
{original_text}

СУММАРИЗАЦИЯ:
{summary_text}

КРИТЕРИИ ОЦЕНКИ:

1. ПОЛНОТА (coverage): Все ли ключевые темы из оригинала покрыты в суммари?
   - 1.0 = все темы покрыты
   - 0.5 = половина тем покрыта
   - 0.0 = ничего не покрыто

2. ТОЧНОСТЬ (accuracy): Нет ли искажений, галлюцинаций, ложной информации?
   - 1.0 = полностью точно
   - 0.5 = есть небольшие искажения
   - 0.0 = много ошибок

3. СВЯЗНОСТЬ (coherence): Насколько читабелен и логичен текст?
   - 1.0 = отличная связность
   - 0.5 = приемлемо
   - 0.0 = нечитабельно

4. ИНФОРМАТИВНОСТЬ (informativeness): Сколько полезной информации на единицу текста?
   - 1.0 = высокая плотность информации
   - 0.5 = средняя
   - 0.0 = низкая

5. ОБЩАЯ ОЦЕНКА (overall): Твоя итоговая оценка качества.

ВАЖНО: Верни ТОЛЬКО JSON в следующем формате (без дополнительного текста):
{{
  "coverage": 0.85,
  "accuracy": 0.95,
  "coherence": 0.90,
  "informativeness": 0.80,
  "overall": 0.87,
  "explanation": "Краткое объяснение оценки"
}}"""

    # English version
    return f"""Evaluate the summary quality based on 5 criteria (score 0.0 to 1.0):

ORIGINAL TEXT:
{original_text}

SUMMARY:
{summary_text}

EVALUATION CRITERIA:

1. COVERAGE: Are all key topics from original covered?
   - 1.0 = all topics covered
   - 0.5 = half covered
   - 0.0 = nothing covered

2. ACCURACY: No distortions, hallucinations, or false information?
   - 1.0 = fully accurate
   - 0.5 = minor distortions
   - 0.0 = many errors

3. COHERENCE: How readable and logical is the text?
   - 1.0 = excellent coherence
   - 0.5 = acceptable
   - 0.0 = unreadable

4. INFORMATIVENESS: Information density per unit of text?
   - 1.0 = high density
   - 0.5 = medium
   - 0.0 = low

5. OVERALL: Your final quality rating.

IMPORTANT: Return ONLY JSON in this format (no extra text):
{{
  "coverage": 0.85,
  "accuracy": 0.95,
  "coherence": 0.90,
  "informativeness": 0.80,
  "overall": 0.87,
  "explanation": "Brief explanation"
}}"""
