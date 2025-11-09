"""Code quality checker domain service."""

from typing import List

from src.domain.value_objects.quality_metrics import Metrics, QualityScore


class CodeQualityChecker:
    """Service for checking code quality."""

    @staticmethod
    def check_readability(code: str) -> QualityScore:
        """
        Check code readability.

        Args:
            code: Code to analyze

        Returns:
            Readability quality score
        """
        if not code:
            return QualityScore(score=0.0, metric_name="readability")

        lines = code.split("\n")
        total_lines = len(lines)
        long_lines = sum(1 for line in lines if len(line) > 120)

        readability = 1.0 - (long_lines / max(total_lines, 1))
        return QualityScore(score=max(0.0, readability), metric_name="readability")

    @staticmethod
    def check_structure(code: str) -> QualityScore:
        """
        Check code structure quality.

        Args:
            code: Code to analyze

        Returns:
            Structure quality score
        """
        if not code:
            return QualityScore(score=0.0, metric_name="structure")

        total_chars = len(code)
        functions = code.count("def ")
        classes = code.count("class ")

        if total_chars == 0:
            return QualityScore(score=0.0, metric_name="structure")

        structure_score = min(1.0, (functions + classes * 2) / (total_chars / 100))
        return QualityScore(score=structure_score, metric_name="structure")

    @staticmethod
    def check_comments(code: str) -> QualityScore:
        """
        Check code commenting.

        Args:
            code: Code to analyze

        Returns:
            Comments quality score
        """
        if not code:
            return QualityScore(score=0.0, metric_name="comments")

        lines = code.split("\n")
        total_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if "#" in line])

        if total_lines == 0:
            return QualityScore(score=0.0, metric_name="comments")

        comment_ratio = comment_lines / total_lines
        return QualityScore(score=min(1.0, comment_ratio * 2), metric_name="comments")

    @staticmethod
    def calculate_overall_metrics(code: str) -> Metrics:
        """
        Calculate overall code quality metrics.

        Args:
            code: Code to analyze

        Returns:
            Comprehensive metrics
        """
        scores = {
            "readability": CodeQualityChecker.check_readability(code).score,
            "structure": CodeQualityChecker.check_structure(code).score,
            "comments": CodeQualityChecker.check_comments(code).score,
        }

        overall_score = sum(scores.values()) / len(scores)
        return Metrics(scores=scores, overall_score=overall_score)

    @staticmethod
    def get_quality_scores(code: str) -> List[QualityScore]:
        """
        Get all quality scores for code.

        Args:
            code: Code to analyze

        Returns:
            List of quality scores
        """
        return [
            CodeQualityChecker.check_readability(code),
            CodeQualityChecker.check_structure(code),
            CodeQualityChecker.check_comments(code),
        ]
