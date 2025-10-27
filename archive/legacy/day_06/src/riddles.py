"""
Module with logical riddles and analysis logic.

Contains riddles from requirements and functions for analyzing model responses.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import re

from .constants import LOGICAL_KEYWORDS, STEP_PATTERNS, DIFFICULTY_LEVELS


@dataclass
class Riddle:
    """Riddle structure."""
    title: str
    text: str
    difficulty: int  # 1-5, where 5 is the most difficult


class RiddleAnalyzer:
    """Analyzer for riddle responses."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def analyze_response(self, response: str) -> Dict[str, Any]:
        """
        Analyze model response.
        
        Args:
            response: Model response text
            
        Returns:
            Dict: Analysis results
        """
        return {
            "word_count": self._count_words(response),
            "has_logical_keywords": self._has_logical_keywords(response),
            "logical_keywords_count": self._count_logical_keywords(response),
            "has_step_by_step": self._has_step_by_step_structure(response),
            "response_length": len(response)
        }
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def _has_logical_keywords(self, text: str) -> bool:
        """Check for logical keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in LOGICAL_KEYWORDS)
    
    def _count_logical_keywords(self, text: str) -> int:
        """Count logical keywords."""
        text_lower = text.lower()
        count = 0
        for keyword in LOGICAL_KEYWORDS:
            count += text_lower.count(keyword)
        return count
    
    def _has_step_by_step_structure(self, text: str) -> bool:
        """Check for step-by-step structure."""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in STEP_PATTERNS)


class RiddleCollection:
    """Collection of riddles from requirements."""
    
    def __init__(self):
        """Initialize riddle collection."""
        self.riddles = self._create_riddles()
    
    def _create_riddles(self) -> List[Riddle]:
        """Create list of riddles according to requirements."""
        return [
            Riddle(
                title="Coin and kitten riddle",
                text="You enter a room and see a coin and a kitten. You take the coin and leave. What remains in the room?",
                difficulty=1
            ),
            Riddle(
                title="Classic train riddle",
                text="A train leaves point A at 9 AM, and another leaves point B at the same time towards the first. Who will be closer to point A when they meet?",
                difficulty=2
            ),
            Riddle(
                title="Three doors riddle",
                text="You have three doors: behind one is a prize, behind others is nothing. You choose one, the host opens an empty one from the remaining and offers to change your choice. What is more profitable?",
                difficulty=3
            ),
            Riddle(
                title="Two envelopes paradox",
                text="In one envelope there is amount X, in another - 2X. You choose one. Should you change? Why?",
                difficulty=4
            ),
            Riddle(
                title="Wise men with colored hats",
                text="Three wise men see each other's heads, know that each hat is white or blue, and hear that at least one is white. They say 'I don't know' in turn. What can they conclude?",
                difficulty=5
            )
        ]
    
    def get_riddles(self) -> List[Riddle]:
        """Get list of all riddles."""
        return self.riddles
    
    def get_riddle_texts(self) -> List[str]:
        """Get texts of all riddles."""
        return [riddle.text for riddle in self.riddles]
    
    def get_riddle_by_difficulty(self, difficulty: int) -> List[Riddle]:
        """
        Get riddles by difficulty level.
        
        Args:
            difficulty: Difficulty level (1-5)
            
        Returns:
            List[Riddle]: Riddles of specified difficulty
        """
        return [riddle for riddle in self.riddles if riddle.difficulty == difficulty]
