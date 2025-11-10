"""Quality checker for summarization results."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.domain.services.text_cleaner import TextCleanerService


@dataclass
class QualityScore:
    """Quality score for a summary.

    Args:
        score: Overall quality score (0.0-1.0).
        length_score: Score based on length appropriateness (0.0-1.0).
        sentence_count_score: Score based on sentence count (0.0-1.0).
        uniqueness_score: Score based on sentence uniqueness (0.0-1.0).
        coherence_score: Score based on coherence (0.0-1.0).
        issues: List of quality issues found.
    """

    score: float
    length_score: float
    sentence_count_score: float
    uniqueness_score: float
    coherence_score: float
    issues: list[str]

    def __post_init__(self) -> None:
        """Validate quality score."""
        for field_name, value in [
            ("score", self.score),
            ("length_score", self.length_score),
            ("sentence_count_score", self.sentence_count_score),
            ("uniqueness_score", self.uniqueness_score),
            ("coherence_score", self.coherence_score),
        ]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{field_name} must be between 0.0 and 1.0, got {value}"
                )


class SummaryQualityChecker:
    """Service for checking summary quality.

    Purpose:
        Validates summaries for length, sentence count, uniqueness,
        and coherence. Provides quality scores and retry recommendations.
    """

    def __init__(
        self,
        min_length: int = 20,
        min_sentences: int = 1,
        sentence_similarity_threshold: float = 0.6,
    ) -> None:
        """Initialize quality checker.

        Args:
            min_length: Minimum summary length in characters.
            min_sentences: Minimum number of sentences.
            sentence_similarity_threshold: Threshold for duplicate detection.
        """
        self.min_length = min_length
        self.min_sentences = min_sentences
        self.sentence_similarity_threshold = sentence_similarity_threshold

    def check_quality(
        self,
        summary: str,
        source_text: str,
        expected_sentences: int,
    ) -> QualityScore:
        """Check quality of a summary.

        Purpose:
            Evaluates summary on multiple dimensions and returns
            a quality score with specific issue reports.

        Args:
            summary: Summary text to check.
            source_text: Original source text (for length comparison).
            expected_sentences: Expected number of sentences.

        Returns:
            QualityScore with overall score and sub-scores.
        """
        issues: list[str] = []

        # Length check
        length_score = self._check_length(summary, issues)

        # Sentence count check
        sentences = self._split_sentences(summary)
        sentence_count_score = self._check_sentence_count(
            len(sentences), expected_sentences, issues
        )

        # Uniqueness check
        unique_sentences = TextCleanerService.deduplicate_sentences(
            sentences, threshold=self.sentence_similarity_threshold
        )
        uniqueness_score = self._check_uniqueness(
            len(sentences), len(unique_sentences), issues
        )

        # Coherence check (basic)
        coherence_score = self._check_coherence(summary, issues)

        # Overall score (weighted average)
        overall_score = (
            length_score * 0.25
            + sentence_count_score * 0.25
            + uniqueness_score * 0.25
            + coherence_score * 0.25
        )

        return QualityScore(
            score=overall_score,
            length_score=length_score,
            sentence_count_score=sentence_count_score,
            uniqueness_score=uniqueness_score,
            coherence_score=coherence_score,
            issues=issues,
        )

    def should_retry(self, quality: QualityScore, min_quality: float = 0.6) -> bool:
        """Determine if summary should be retried.

        Args:
            quality: Quality score to evaluate.
            min_quality: Minimum acceptable quality score (default: 0.6).

        Returns:
            True if summary quality is below threshold.
        """
        return quality.score < min_quality

    def _check_length(self, summary: str, issues: list[str]) -> float:
        """Check summary length appropriateness.

        Args:
            summary: Summary text.
            issues: List to append issues to.

        Returns:
            Length score (0.0-1.0).
        """
        if len(summary) < self.min_length:
            issues.append(
                f"Summary too short ({len(summary)} chars, min: {self.min_length})"
            )
            return 0.0

        # Score based on length (between min and ideal)
        ideal_length = 500  # Reasonable default
        if len(summary) < ideal_length:
            # Linear scale from min_length to ideal_length
            return min(
                1.0, (len(summary) - self.min_length) / (ideal_length - self.min_length)
            )
        else:
            # Slight penalty for very long summaries, but still acceptable
            return max(0.7, 1.0 - (len(summary) - ideal_length) / ideal_length)

    def _check_sentence_count(
        self, actual_count: int, expected_count: int, issues: list[str]
    ) -> float:
        """Check sentence count.

        Args:
            actual_count: Actual number of sentences.
            expected_count: Expected number of sentences.
            issues: List to append issues to.

        Returns:
            Sentence count score (0.0-1.0).
        """
        if actual_count < self.min_sentences:
            issues.append(
                f"Too few sentences ({actual_count}, min: {self.min_sentences})"
            )
            return 0.0

        if actual_count == 0:
            issues.append("No sentences found")
            return 0.0

        # Score based on how close to expected
        ratio = actual_count / expected_count if expected_count > 0 else 1.0

        if 0.8 <= ratio <= 1.2:
            # Within 20% of expected is good
            return 1.0
        elif 0.5 <= ratio < 0.8 or 1.2 < ratio <= 1.5:
            # Within 50% is acceptable
            return 0.7
        else:
            issues.append(
                f"Sentence count mismatch ({actual_count} vs expected {expected_count})"
            )
            return 0.5

    def _check_uniqueness(
        self, total_sentences: int, unique_sentences: int, issues: list[str]
    ) -> float:
        """Check sentence uniqueness.

        Args:
            total_sentences: Total number of sentences.
            unique_sentences: Number of unique sentences.
            issues: List to append issues to.

        Returns:
            Uniqueness score (0.0-1.0).
        """
        if total_sentences == 0:
            return 0.0

        uniqueness_ratio = unique_sentences / total_sentences

        if uniqueness_ratio < 0.7:
            issues.append(
                f"Low uniqueness ({uniqueness_ratio:.1%}, "
                f"{total_sentences - unique_sentences} duplicates)"
            )
            return uniqueness_ratio
        else:
            return 1.0

    def _check_coherence(self, summary: str, issues: list[str]) -> float:
        """Check summary coherence (basic checks).

        Args:
            summary: Summary text.
            issues: List to append issues to.

        Returns:
            Coherence score (0.0-1.0).
        """
        # Basic coherence checks:
        # 1. Not just punctuation
        if not re.search(r"[А-Яа-яA-Za-z]", summary):
            issues.append("Summary contains no letters (only punctuation)")
            return 0.0

        # 2. Has sentence endings
        sentences = self._split_sentences(summary)
        if len(sentences) > 0:
            # Check that sentences end properly
            proper_endings = sum(
                1 for s in sentences if s.rstrip().endswith((".", "!", "?"))
            )
            if proper_endings < len(sentences) * 0.8:
                issues.append("Many sentences missing proper endings")
                return 0.7

        # 3. Not too many repeated words (simple check)
        words = summary.lower().split()
        if len(words) > 0:
            unique_words = set(words)
            word_diversity = len(unique_words) / len(words)
            if word_diversity < 0.3:
                issues.append("Low word diversity (many repeated words)")
                return 0.6

        return 1.0

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        # Simple sentence splitting
        pattern = r"[.!?…]+"
        sentences = re.split(pattern, text.strip())
        return [s.strip() for s in sentences if s.strip()]
