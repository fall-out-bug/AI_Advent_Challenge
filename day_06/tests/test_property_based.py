"""
Property-based tests for edge cases.

Following Python Zen: "Errors should never pass silently"
and comprehensive testing principles.
"""

import pytest
from hypothesis import given, strategies as st
from typing import List, Dict, Any

from src.riddles import RiddleAnalyzer
from src.constants import LOGICAL_KEYWORDS, STEP_PATTERNS


class TestPropertyBasedRiddleAnalyzer:
    """Property-based tests for RiddleAnalyzer."""
    
    @given(text=st.text(min_size=0, max_size=1000))
    def test_word_count_properties(self, text):
        """
        Test word count properties.
        
        Properties:
        - Word count should never be negative
        - Word count should equal number of space-separated words
        """
        analyzer = RiddleAnalyzer()
        word_count = analyzer._count_words(text)
        
        # Property 1: Word count should never be negative
        assert word_count >= 0
        
        # Property 2: Word count should equal number of space-separated words
        expected_count = len(text.split()) if text else 0
        assert word_count == expected_count
    
    @given(text=st.text(min_size=0, max_size=1000))
    def test_logical_keywords_properties(self, text):
        """
        Test logical keywords properties.
        
        Properties:
        - Logical keyword count should never be negative
        - If text contains logical keywords, has_logical_keywords should be True
        - Keyword count should be consistent with has_logical_keywords
        """
        analyzer = RiddleAnalyzer()
        keyword_count = analyzer._count_logical_keywords(text)
        has_keywords = analyzer._has_logical_keywords(text)
        
        # Property 1: Count should never be negative
        assert keyword_count >= 0
        
        # Property 2: Consistency between count and boolean
        if keyword_count > 0:
            assert has_keywords is True
        else:
            assert has_keywords is False
    
    @given(text=st.text(min_size=0, max_size=1000))
    def test_step_structure_properties(self, text):
        """
        Test step structure properties.
        
        Properties:
        - Step structure detection should be consistent
        - Empty text should not have step structure
        """
        analyzer = RiddleAnalyzer()
        has_structure = analyzer._has_step_by_step_structure(text)
        
        # Property 1: Empty text should not have step structure
        if not text.strip():
            assert has_structure is False
        
        # Property 2: If text contains step patterns, should detect structure
        text_lower = text.lower()
        has_pattern = any(pattern in text_lower for pattern in [
            "1.", "2.", "1)", "2)", "шаг 1", "этап 1", "сначала", "затем", "далее", "в итоге"
        ])
        
        if has_pattern:
            assert has_structure is True
    
    @given(text=st.text(min_size=0, max_size=1000))
    def test_analyze_response_properties(self, text):
        """
        Test analyze_response properties.
        
        Properties:
        - Analysis should always return a dict with required keys
        - All numeric values should be non-negative
        - Response length should match input length
        """
        analyzer = RiddleAnalyzer()
        analysis = analyzer.analyze_response(text)
        
        # Property 1: Should return dict with required keys
        required_keys = [
            "word_count", "has_logical_keywords", "logical_keywords_count",
            "has_step_by_step", "response_length"
        ]
        for key in required_keys:
            assert key in analysis
        
        # Property 2: Numeric values should be non-negative
        assert analysis["word_count"] >= 0
        assert analysis["logical_keywords_count"] >= 0
        assert analysis["response_length"] >= 0
        
        # Property 3: Response length should match input length
        assert analysis["response_length"] == len(text)
        
        # Property 4: Boolean values should be actual booleans
        assert isinstance(analysis["has_logical_keywords"], bool)
        assert isinstance(analysis["has_step_by_step"], bool)
    
    @given(text=st.text(min_size=0, max_size=1000))
    def test_consistency_properties(self, text):
        """
        Test consistency between different analysis methods.
        
        Properties:
        - Word count from analyze_response should match direct count
        - Logical keyword detection should be consistent
        """
        analyzer = RiddleAnalyzer()
        analysis = analyzer.analyze_response(text)
        direct_word_count = analyzer._count_words(text)
        direct_has_keywords = analyzer._has_logical_keywords(text)
        
        # Property 1: Word count consistency
        assert analysis["word_count"] == direct_word_count
        
        # Property 2: Logical keywords consistency
        assert analysis["has_logical_keywords"] == direct_has_keywords


class TestPropertyBasedConstants:
    """Property-based tests for constants."""
    
    @given(text=st.text(min_size=0, max_size=100))
    def test_logical_keywords_properties(self, text):
        """
        Test logical keywords properties.
        
        Properties:
        - All keywords should be non-empty strings
        - Keywords should be lowercase
        - No duplicate keywords
        """
        # Property 1: All keywords should be non-empty strings
        for keyword in LOGICAL_KEYWORDS:
            assert isinstance(keyword, str)
            assert len(keyword) > 0
        
        # Property 2: Keywords should be lowercase
        for keyword in LOGICAL_KEYWORDS:
            assert keyword.islower()
        
        # Property 3: No duplicate keywords
        assert len(LOGICAL_KEYWORDS) == len(set(LOGICAL_KEYWORDS))
    
    @given(text=st.text(min_size=0, max_size=100))
    def test_step_patterns_properties(self, text):
        """
        Test step patterns properties.
        
        Properties:
        - All patterns should be valid regex strings
        - Patterns should be non-empty
        """
        import re
        
        # Property 1: All patterns should be non-empty strings
        for pattern in STEP_PATTERNS:
            assert isinstance(pattern, str)
            assert len(pattern) > 0
        
        # Property 2: Patterns should be valid regex
        for pattern in STEP_PATTERNS:
            try:
                re.compile(pattern)
            except re.error:
                pytest.fail(f"Invalid regex pattern: {pattern}")


class TestPropertyBasedEdgeCases:
    """Property-based tests for edge cases."""
    
    @given(text=st.text(alphabet=" \t\n\r", min_size=0, max_size=100))
    def test_whitespace_only_text(self, text):
        """
        Test analyzer with whitespace-only text.
        
        Properties:
        - Whitespace-only text should have word count 0
        - Should not have logical keywords or step structure
        """
        analyzer = RiddleAnalyzer()
        analysis = analyzer.analyze_response(text)
        
        assert analysis["word_count"] == 0
        assert analysis["has_logical_keywords"] is False
        assert analysis["logical_keywords_count"] == 0
        assert analysis["has_step_by_step"] is False
    
    @given(text=st.text(alphabet="абвгдеёжзийклмнопрстуфхцчшщъыьэюя", min_size=0, max_size=100))
    def test_cyrillic_text(self, text):
        """
        Test analyzer with Cyrillic text.
        
        Properties:
        - Should handle Cyrillic characters correctly
        - Analysis should be consistent
        """
        analyzer = RiddleAnalyzer()
        analysis = analyzer.analyze_response(text)
        
        # All properties should still hold
        assert analysis["word_count"] >= 0
        assert analysis["logical_keywords_count"] >= 0
        assert analysis["response_length"] == len(text)
        assert isinstance(analysis["has_logical_keywords"], bool)
        assert isinstance(analysis["has_step_by_step"], bool)
    
    @given(text=st.text(min_size=0, max_size=10))
    def test_very_short_text(self, text):
        """
        Test analyzer with very short text.
        
        Properties:
        - Should handle very short text correctly
        - Analysis should be consistent
        """
        analyzer = RiddleAnalyzer()
        analysis = analyzer.analyze_response(text)
        
        # All properties should still hold
        assert analysis["word_count"] >= 0
        assert analysis["logical_keywords_count"] >= 0
        assert analysis["response_length"] == len(text)
        assert isinstance(analysis["has_logical_keywords"], bool)
        assert isinstance(analysis["has_step_by_step"], bool)
