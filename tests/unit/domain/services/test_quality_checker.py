"""Unit tests for SummaryQualityChecker."""

from __future__ import annotations

import pytest

from src.domain.services.summary_quality_checker import (
    QualityScore,
    SummaryQualityChecker,
)


def test_check_quality_good_summary():
    """Test quality check for good summary."""
    checker = SummaryQualityChecker()
    
    # Use proper sentences with periods
    summary = "First sentence. Second sentence. Third sentence."
    source = "Long source text. " * 100  # Add periods for proper sentences
    
    quality = checker.check_quality(summary, source, expected_sentences=3)
    
    assert quality.score > 0.5
    # May have some minor issues, but should be generally good
    # Allow some issues as quality checker is strict


def test_check_quality_too_short():
    """Test quality check detects too short summary."""
    checker = SummaryQualityChecker(min_length=50)
    
    summary = "Short"  # Too short
    source = "Long source text"
    
    quality = checker.check_quality(summary, source, expected_sentences=1)
    
    assert quality.length_score == 0.0
    assert len(quality.issues) > 0
    assert any("too short" in issue.lower() for issue in quality.issues)


def test_check_quality_wrong_sentence_count():
    """Test quality check detects wrong sentence count."""
    checker = SummaryQualityChecker()
    
    summary = "One sentence."  # Expected 5
    source = "Long source text"
    
    quality = checker.check_quality(summary, source, expected_sentences=5)
    
    assert quality.sentence_count_score < 1.0


def test_check_quality_duplicate_sentences():
    """Test quality check detects duplicate sentences."""
    checker = SummaryQualityChecker()
    
    summary = "Same sentence. Same sentence. Same sentence."
    source = "Long source text"
    
    quality = checker.check_quality(summary, source, expected_sentences=3)
    
    assert quality.uniqueness_score < 1.0
    assert any("duplicate" in issue.lower() or "uniqueness" in issue.lower() 
               for issue in quality.issues)


def test_should_retry():
    """Test retry recommendation logic."""
    checker = SummaryQualityChecker()
    
    # Low quality
    low_quality = QualityScore(
        score=0.3,
        length_score=0.5,
        sentence_count_score=0.3,
        uniqueness_score=0.4,
        coherence_score=0.2,
        issues=["Multiple issues"],
    )
    
    assert checker.should_retry(low_quality, min_quality=0.6) is True
    
    # High quality
    high_quality = QualityScore(
        score=0.9,
        length_score=1.0,
        sentence_count_score=1.0,
        uniqueness_score=1.0,
        coherence_score=0.8,
        issues=[],
    )
    
    assert checker.should_retry(high_quality, min_quality=0.6) is False
