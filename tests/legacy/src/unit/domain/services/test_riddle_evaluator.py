"""Tests for riddle evaluator domain service.

Following TDD approach:
- Write tests first (red)
- Implement minimal code (green)
- Refactor for clarity (refactor)
"""

from src.domain.services.riddle_evaluator import RiddleEvaluator


class TestRiddleEvaluator:
    """Test riddle evaluator domain service."""

    def test_evaluator_can_initialize(self):
        """Test that evaluator can be initialized."""
        evaluator = RiddleEvaluator()

        assert evaluator is not None

    def test_evaluator_has_riddles(self):
        """Test that evaluator has a collection of riddles."""
        evaluator = RiddleEvaluator()

        riddles = evaluator.get_all_riddles()

        assert len(riddles) > 0
        assert isinstance(riddles[0], dict)
        assert "title" in riddles[0]
        assert "text" in riddles[0]
        assert "difficulty" in riddles[0]

    def test_evaluator_analyzes_response(self):
        """Test that evaluator can analyze model responses."""
        evaluator = RiddleEvaluator()

        response = "First, I need to think step by step. Then I'll provide the answer."
        analysis = evaluator.analyze_response(response)

        assert isinstance(analysis, dict)
        assert "word_count" in analysis
        assert "has_logical_keywords" in analysis
        assert "has_step_by_step" in analysis

    def test_evaluator_detects_logical_keywords(self):
        """Test that evaluator detects logical keywords."""
        evaluator = RiddleEvaluator()

        response_with_keywords = "Let's analyze: first, second, therefore, conclusion."
        analysis = evaluator.analyze_response(response_with_keywords)

        assert analysis["has_logical_keywords"] is True
        assert analysis["logical_keywords_count"] > 0

    def test_evaluator_detects_step_by_step(self):
        """Test that evaluator detects step-by-step structure."""
        evaluator = RiddleEvaluator()

        response_with_steps = (
            "Step 1: Consider X. Step 2: Consider Y. Step 3: Conclusion."
        )
        analysis = evaluator.analyze_response(response_with_steps)

        assert analysis["has_step_by_step"] is True

    def test_evaluator_counts_words(self):
        """Test that evaluator counts words correctly."""
        evaluator = RiddleEvaluator()

        response = "This is a test response example"
        analysis = evaluator.analyze_response(response)

        assert analysis["word_count"] == 6

    def test_evaluator_filters_by_difficulty(self):
        """Test that evaluator can filter riddles by difficulty."""
        evaluator = RiddleEvaluator()

        easy_riddles = evaluator.get_riddles_by_difficulty(1)
        hard_riddles = evaluator.get_riddles_by_difficulty(5)

        assert all(r["difficulty"] == 1 for r in easy_riddles)
        assert all(r["difficulty"] == 5 for r in hard_riddles)
