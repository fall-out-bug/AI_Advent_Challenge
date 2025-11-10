"""Tests for code quality checker service."""

from src.domain.services.code_quality_checker import CodeQualityChecker
from src.domain.value_objects.quality_metrics import Metrics, QualityScore


def test_check_readability() -> None:
    """Test readability check."""
    code = "def hello():\n    print('world')"
    score = CodeQualityChecker.check_readability(code)
    assert isinstance(score, QualityScore)
    assert score.metric_name == "readability"
    assert 0.0 <= score.score <= 1.0


def test_check_structure() -> None:
    """Test structure check."""
    code = "def hello():\n    pass\n\nclass Test:\n    pass"
    score = CodeQualityChecker.check_structure(code)
    assert isinstance(score, QualityScore)
    assert score.metric_name == "structure"
    assert 0.0 <= score.score <= 1.0


def test_check_comments() -> None:
    """Test comments check."""
    code = "# This is a comment\ndef hello():\n    pass  # Another comment"
    score = CodeQualityChecker.check_comments(code)
    assert isinstance(score, QualityScore)
    assert score.metric_name == "comments"
    assert 0.0 <= score.score <= 1.0


def test_calculate_overall_metrics() -> None:
    """Test overall metrics calculation."""
    code = "def hello():\n    print('world')  # Comment"
    metrics = CodeQualityChecker.calculate_overall_metrics(code)
    assert isinstance(metrics, Metrics)
    assert 0.0 <= metrics.overall_score <= 1.0
    assert "readability" in metrics.scores
    assert "structure" in metrics.scores
    assert "comments" in metrics.scores


def test_empty_code() -> None:
    """Test with empty code."""
    metrics = CodeQualityChecker.calculate_overall_metrics("")
    assert metrics.overall_score == 0.0
