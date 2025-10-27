"""
Tests for utils/text_utils.py module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest

from utils.text_utils import contains_any, normalize_for_trigger


class TestTextUtils:
    """Test text utilities functionality."""
    
    def test_contains_any_found(self):
        """Test contains_any when needles are found."""
        haystack = "Hello world"
        needles = ["world", "universe"]
        
        result = contains_any(haystack, needles)
        
        assert result is True
    
    def test_contains_any_not_found(self):
        """Test contains_any when needles are not found."""
        haystack = "Hello world"
        needles = ["universe", "galaxy"]
        
        result = contains_any(haystack, needles)
        
        assert result is False
    
    def test_contains_any_case_insensitive(self):
        """Test contains_any is case insensitive."""
        haystack = "Hello WORLD"
        needles = ["world", "universe"]
        
        result = contains_any(haystack, needles)
        
        assert result is True
    
    def test_contains_any_empty_haystack(self):
        """Test contains_any with empty haystack."""
        haystack = ""
        needles = ["world", "universe"]
        
        result = contains_any(haystack, needles)
        
        assert result is False
    
    def test_contains_any_empty_needles(self):
        """Test contains_any with empty needles list."""
        haystack = "Hello world"
        needles = []
        
        result = contains_any(haystack, needles)
        
        assert result is False
    
    def test_normalize_for_trigger_basic(self):
        """Test basic normalization."""
        text = "Hello, world!"
        
        result = normalize_for_trigger(text)
        
        assert result == "hello world"
    
    def test_normalize_for_trigger_unicode(self):
        """Test normalization with unicode characters."""
        text = "Hello—world"  # em dash
        
        result = normalize_for_trigger(text)
        
        assert result == "hello world"
    
    def test_normalize_for_trigger_quotes(self):
        """Test normalization with various quote types."""
        text = 'Hello "world" and \'universe\''
        
        result = normalize_for_trigger(text)
        
        assert result == "hello world and universe"
    
    def test_normalize_for_trigger_punctuation(self):
        """Test normalization with various punctuation."""
        text = "Hello: world; universe!"
        
        result = normalize_for_trigger(text)
        
        assert result == "hello world universe"
    
    def test_normalize_for_trigger_brackets(self):
        """Test normalization with brackets."""
        text = "Hello (world) [universe] {galaxy}"
        
        result = normalize_for_trigger(text)
        
        assert result == "hello world universe galaxy"
    
    def test_normalize_for_trigger_multiple_spaces(self):
        """Test normalization with multiple spaces."""
        text = "Hello    world   universe"
        
        result = normalize_for_trigger(text)
        
        assert result == "hello world universe"
    
    def test_normalize_for_trigger_empty_string(self):
        """Test normalization with empty string."""
        text = ""
        
        result = normalize_for_trigger(text)
        
        assert result == ""
    
    def test_normalize_for_trigger_none(self):
        """Test normalization with None."""
        text = None
        
        result = normalize_for_trigger(text)
        
        assert result == ""
    
    def test_normalize_for_trigger_complex(self):
        """Test normalization with complex text."""
        text = "Hello—world! How are you? I'm fine, thank you."
        
        result = normalize_for_trigger(text)
        
        assert result == "hello world how are you i m fine thank you"
    
    def test_normalize_for_trigger_mixed_separators(self):
        """Test normalization with mixed separators."""
        text = "Hello-world|universe,galaxy;star:planet"
        
        result = normalize_for_trigger(text)
        
        assert result == "hello world universe galaxy star planet"
