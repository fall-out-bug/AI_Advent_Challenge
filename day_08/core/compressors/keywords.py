"""
Keywords compression strategy.

Compresses text by extracting and keeping only
important keywords (words longer than 4 characters).
"""

from typing import List
from core.compressors.base import BaseCompressor


class KeywordsCompressor(BaseCompressor):
    """
    Keywords compression strategy.
    
    Extracts words longer than 4 characters and keeps
    first N keywords to fit within token limit.
    """
    
    def _perform_compression(
        self, 
        text: str, 
        max_tokens: int, 
        model_name: str
    ) -> str:
        """
        Perform keywords compression.
        
        Args:
            text: Input text to compress
            max_tokens: Maximum allowed tokens
            model_name: Name of the model
            
        Returns:
            str: Compressed text
        """
        keywords = self._extract_keywords(text)
        max_words = self._calculate_word_budget(max_tokens)
        selected = self._select_top_keywords(keywords, max_words)
        
        return self._join_keywords(selected)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        words = text.split()
        return [word for word in words if len(word) > 4 and word.isalpha()]
    
    def _calculate_word_budget(self, max_tokens: int) -> int:
        """Calculate maximum words allowed."""
        return int(max_tokens / 1.3)
    
    def _select_top_keywords(self, keywords: List[str], max_words: int) -> List[str]:
        """Select top keywords up to max_words limit."""
        return keywords[:max_words]
    
    def _join_keywords(self, keywords: List[str]) -> str:
        """Join keywords into compressed text."""
        return " ".join(keywords)
    
    def _get_strategy_name(self) -> str:
        """Get strategy name."""
        return "keywords"
