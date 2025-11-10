"""Riddle evaluator domain service.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

import re
from typing import Any, Dict, List

# Logical keywords for analyzing responses
LOGICAL_KEYWORDS = [
    "first",
    "second",
    "third",
    "therefore",
    "conclusion",
    "analyze",
    "consider",
    "assume",
    "given",
    "if",
    "then",
    "because",
    "since",
    "thus",
    "hence",
    "however",
    "also",
    "additionally",
    "furthermore",
    "moreover",
    "step",
    "steps",
    "reasoning",
    "logic",
    "logical",
    "based on",
    "according to",
]

# Patterns for step-by-step analysis
STEP_PATTERNS = [
    r"step\s+\d+",
    r"step\s+one",
    r"first\s+step",
    r"step\s+1",
    r"\d+\.\s+",  # Numbered list
]


class RiddleEvaluator:
    """
    Evaluator for analyzing model responses to logical riddles.

    Provides functionality to:
    - Analyze response quality
    - Detect logical reasoning
    - Identify step-by-step structure
    - Assess response completeness
    """

    def __init__(self):
        """Initialize riddle evaluator."""
        self.riddles = self._create_riddles()
        self.logical_keywords = LOGICAL_KEYWORDS
        self.step_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in STEP_PATTERNS
        ]

    def get_all_riddles(self) -> List[Dict[str, Any]]:
        """
        Get all riddles.

        Returns:
            List of riddle dictionaries
        """
        return [
            {
                "title": riddle["title"],
                "text": riddle["text"],
                "difficulty": riddle["difficulty"],
            }
            for riddle in self.riddles
        ]

    def get_riddles_by_difficulty(self, difficulty: int) -> List[Dict[str, Any]]:
        """
        Get riddles by difficulty level.

        Args:
            difficulty: Difficulty level (1-5)

        Returns:
            List of riddles of specified difficulty
        """
        return [r for r in self.get_all_riddles() if r["difficulty"] == difficulty]

    def analyze_response(self, response: str) -> Dict[str, Any]:
        """
        Analyze model response for logical reasoning quality.

        Args:
            response: Model response text

        Returns:
            Dictionary with analysis results:
            - word_count: Number of words
            - has_logical_keywords: Boolean
            - logical_keywords_count: Integer
            - has_step_by_step: Boolean
            - response_length: Integer
        """
        return {
            "word_count": self._count_words(response),
            "has_logical_keywords": self._has_logical_keywords(response),
            "logical_keywords_count": self._count_logical_keywords(response),
            "has_step_by_step": self._has_step_by_step_structure(response),
            "response_length": len(response),
        }

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())

    def _has_logical_keywords(self, text: str) -> bool:
        """Check if text contains logical keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.logical_keywords)

    def _count_logical_keywords(self, text: str) -> int:
        """Count occurrences of logical keywords."""
        text_lower = text.lower()
        count = 0
        for keyword in self.logical_keywords:
            count += text_lower.count(keyword)
        return count

    def _has_step_by_step_structure(self, text: str) -> bool:
        """Check if text has step-by-step structure."""
        return any(pattern.search(text) for pattern in self.step_patterns)

    def _create_riddles(self) -> List[Dict[str, Any]]:
        """Create collection of riddles."""
        return [
            {
                "title": "Coin and kitten riddle",
                "text": "You enter a room and see a coin and a kitten. You take the coin and leave. What remains in the room?",
                "difficulty": 1,
            },
            {
                "title": "Classic train riddle",
                "text": "A train leaves point A at 9 AM, and another leaves point B at the same time towards the first. Who will be closer to point A when they meet?",
                "difficulty": 2,
            },
            {
                "title": "Three doors riddle",
                "text": "You have three doors: behind one is a prize, behind others is nothing. You choose one, the host opens an empty one from the remaining and offers to change your choice. What is more profitable?",
                "difficulty": 3,
            },
            {
                "title": "Two envelopes paradox",
                "text": "In one envelope there is amount X, in another - 2X. You choose one. Should you change? Why?",
                "difficulty": 4,
            },
            {
                "title": "Wise men with colored hats",
                "text": "Three wise men see each other's heads, know that each hat is white or blue, and hear that at least one is white. They say 'I don't know' in turn. What can they conclude?",
                "difficulty": 5,
            },
        ]
