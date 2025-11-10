"""Service for evaluating summary quality using LLM as judge."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from src.domain.value_objects.summarization_context import SummarizationContext
from src.domain.value_objects.summarization_evaluation import SummarizationEvaluation
from src.infrastructure.llm.clients.resilient_client import ResilientLLMClient
from src.infrastructure.llm.prompts.evaluation_prompts import get_evaluation_prompt
from src.infrastructure.llm.token_counter import TokenCounter
from src.infrastructure.logging import get_logger

logger = get_logger("summarization_evaluator")


class SummarizationEvaluator:
    """Evaluates summary quality using LLM as judge.

    Purpose:
        Uses Mistral LLM to evaluate summaries based on multiple quality criteria:
        coverage, accuracy, coherence, informativeness, and overall score.

    Example:
        >>> evaluator = SummarizationEvaluator(llm_client, token_counter)
        >>> evaluation = await evaluator.evaluate(
        ...     original_text="Long article...",
        ...     summary_text="Summary...",
        ...     context=context,
        ...     summary_metadata={},
        ... )
        >>> print(evaluation.overall_score)
        0.87
    """

    # Maximum tokens for evaluation prompt
    MAX_ORIGINAL_TOKENS = 2000
    MAX_SUMMARY_TOKENS = 500

    def __init__(
        self,
        llm_client: ResilientLLMClient,
        token_counter: TokenCounter,
    ) -> None:
        """Initialize evaluator.

        Args:
            llm_client: LLM client for evaluation calls.
            token_counter: Token counter for text truncation.
        """
        self._llm_client = llm_client
        self._token_counter = token_counter

    async def evaluate(
        self,
        original_text: str,
        summary_text: str,
        context: SummarizationContext,
        summary_metadata: dict[str, Any],
    ) -> SummarizationEvaluation:
        """Evaluate summary quality using LLM.

        Purpose:
            Generates evaluation prompt, calls LLM, parses JSON response,
            and creates SummarizationEvaluation object.

        Args:
            original_text: Source text that was summarized.
            summary_text: Generated summary text.
            context: Summarization context.
            summary_metadata: Summary result metadata.

        Returns:
            SummarizationEvaluation with quality scores.

        Raises:
            ValueError: If LLM response cannot be parsed or scores are invalid.
        """
        # Truncate if too long
        original_truncated = self._truncate_for_evaluation(original_text)
        summary_truncated = self._truncate_for_evaluation(
            summary_text, max_tokens=self.MAX_SUMMARY_TOKENS
        )

        # Build prompt
        prompt = get_evaluation_prompt(
            original_text=original_truncated,
            summary_text=summary_truncated,
            language=context.language,
        )

        # Call LLM
        try:
            response = await self._llm_client.generate(
                prompt=prompt,
                temperature=0.1,  # Low temp for consistent scoring
                max_tokens=800,
            )
        except Exception as e:
            logger.error(f"Error calling LLM for evaluation: {e}", exc_info=True)
            raise RuntimeError(f"Failed to evaluate summary: {e}") from e

        # Parse scores
        scores = self._parse_scores(response)

        # Generate unique ID
        summary_id = self._generate_id()

        # Create evaluation
        return SummarizationEvaluation(
            summary_id=summary_id,
            original_text=original_text[:5000],  # Store truncated for DB
            summary_text=summary_text,
            coverage_score=scores["coverage"],
            accuracy_score=scores["accuracy"],
            coherence_score=scores["coherence"],
            informativeness_score=scores["informativeness"],
            overall_score=scores["overall"],
            evaluation_method="llm_judge",
            evaluator_model="mistralai/Mistral-7B-Instruct-v0.2",
            evaluation_prompt=prompt,
            raw_response=response,
            summarization_context=self._context_to_dict(context),
            summary_metadata=summary_metadata,
            evaluated_at=datetime.now(timezone.utc),
        )

    def _truncate_for_evaluation(self, text: str, max_tokens: int | None = None) -> str:
        """Truncate text to fit evaluation prompt.

        Args:
            text: Text to truncate.
            max_tokens: Maximum tokens (defaults to MAX_ORIGINAL_TOKENS).

        Returns:
            Truncated text.
        """
        if max_tokens is None:
            max_tokens = self.MAX_ORIGINAL_TOKENS

        tokens = self._token_counter.count_tokens(text)
        if tokens <= max_tokens:
            return text

        # Approximate: 1 token ≈ 4 characters for Russian/English
        max_chars = max_tokens * 4
        truncated = text[:max_chars]

        # Try to truncate at sentence boundary
        last_period = truncated.rfind(".")
        last_exclamation = truncated.rfind("!")
        last_question = truncated.rfind("?")
        last_sentence = max(last_period, last_exclamation, last_question)

        if last_sentence > max_chars * 0.7:
            return truncated[: last_sentence + 1]

        return truncated

    def _parse_scores(self, response: str) -> dict[str, float]:
        """Parse scores from LLM JSON response.

        Args:
            response: LLM response containing JSON.

        Returns:
            Dictionary with coverage, accuracy, coherence, informativeness, overall.

        Raises:
            ValueError: If JSON cannot be parsed or required scores are missing.
        """
        # Try to extract JSON from response
        json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response

        try:
            scores = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {response}")
            raise ValueError(f"Invalid JSON in evaluation response: {e}") from e

        # Validate required fields
        required_fields = [
            "coverage",
            "accuracy",
            "coherence",
            "informativeness",
            "overall",
        ]
        missing_fields = [f for f in required_fields if f not in scores]
        if missing_fields:
            raise ValueError(
                f"Missing required scores in response: {missing_fields}. "
                f"Got: {list(scores.keys())}"
            )

        # Validate scores are in range [0.0, 1.0]
        for field in required_fields:
            score = scores[field]
            if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"Score {field} must be float between 0.0 and 1.0, got {score}"
                )

        return {
            "coverage": float(scores["coverage"]),
            "accuracy": float(scores["accuracy"]),
            "coherence": float(scores["coherence"]),
            "informativeness": float(scores["informativeness"]),
            "overall": float(scores["overall"]),
        }

    def _generate_id(self) -> str:
        """Generate unique evaluation ID.

        Returns:
            Unique string ID.
        """
        return f"eval_{uuid.uuid4().hex[:12]}"

    def _context_to_dict(self, context: SummarizationContext) -> dict[str, Any]:
        """Convert SummarizationContext to dictionary.

        Args:
            context: Context object.

        Returns:
            Dictionary representation.
        """
        return {
            "time_period_hours": context.time_period_hours,
            "source_type": context.source_type,
            "max_chars": context.max_chars,
            "language": context.language,
            "max_sentences": context.max_sentences,
            "user_preferences": context.user_preferences,
            "additional_metadata": context.additional_metadata,
        }
