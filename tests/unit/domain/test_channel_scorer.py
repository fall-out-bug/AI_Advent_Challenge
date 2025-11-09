"""Unit tests for ChannelScorer service.

Following TDD: tests written first before implementation.
"""

from __future__ import annotations

import pytest

from src.domain.services.channel_scorer import ChannelScorer


class TestChannelScorer:
    """Test suite for ChannelScorer."""

    def test_exact_username_match(self) -> None:
        """Test exact username matching."""
        scorer = ChannelScorer()
        query = "onaboka"
        channel = {
            "username": "onaboka",
            "title": "Some Title",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert score > 0.9  # Exact match should be very high

    def test_exact_title_match(self) -> None:
        """Test exact title matching."""
        scorer = ChannelScorer()
        query = "XOR"
        channel = {
            "username": "xor_journal",
            "title": "XOR",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert score > 0.8  # Exact title match should be high

    def test_prefix_username_match(self) -> None:
        """Test prefix username matching."""
        scorer = ChannelScorer()
        query = "onab"
        channel = {
            "username": "onaboka",
            "title": "Some Title",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert score > 0.6  # Prefix match should be decent

    def test_prefix_title_match(self) -> None:
        """Test prefix title matching."""
        scorer = ChannelScorer()
        query = "Крупнокалибер"
        channel = {
            "username": "bolshiepushki",
            "title": "Крупнокалиберный Переполох",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert score > 0.5  # Prefix title match should be decent

    def test_token_overlap_match(self) -> None:
        """Test token overlap matching."""
        scorer = ChannelScorer()
        query = "Набока"
        channel = {
            "username": "onaboka",
            "title": "Набока орёт в борщ",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert score > 0.4  # Token overlap should contribute

    def test_levenshtein_username_match(self) -> None:
        """Test Levenshtein distance for username."""
        scorer = ChannelScorer()
        query = "onabok"  # One char off
        channel = {
            "username": "onaboka",
            "title": "Some Title",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert score > 0.3  # Levenshtein should contribute

    def test_levenshtein_title_match(self) -> None:
        """Test Levenshtein distance for title."""
        scorer = ChannelScorer()
        query = "Крупнокалиберный"
        channel = {
            "username": "bolshiepushki",
            "title": "Крупнокалиберный Переполох",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert score > 0.3  # Levenshtein should contribute

    def test_description_mention_match(self) -> None:
        """Test description mention matching."""
        scorer = ChannelScorer()
        query = "onaboka"
        channel = {
            "username": "some_channel",
            "title": "Some Title",
            "description": "Link @onaboka bot",
        }
        score = scorer.score(query, channel)
        assert score > 0.1  # Description mention should contribute

    def test_no_match(self) -> None:
        """Test no match returns low score."""
        scorer = ChannelScorer()
        query = "completely_different"
        channel = {
            "username": "onaboka",
            "title": "Some Title",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert score < 0.3  # No match should be low

    def test_case_1_onaboka(self) -> None:
        """Test Case 1: onaboka / 'Набока' matching."""
        scorer = ChannelScorer()
        query = "Набока"
        channel = {
            "username": "onaboka",
            "title": "Набока орёт в борщ",
            "description": "Chief Mandezh Officer. Леся Набока — хулиганка...",
        }
        score = scorer.score(query, channel)
        assert score >= 0.6  # Should match reasonably well

    def test_case_2_xor_journal(self) -> None:
        """Test Case 2: xor_journal / 'XOR' matching."""
        scorer = ChannelScorer()
        query = "XOR"
        channel = {
            "username": "xor_journal",
            "title": "XOR",
            "description": "Это журнал о программировании...",
        }
        score = scorer.score(query, channel)
        assert score >= 0.8  # Exact title match should be high

    def test_case_3_bolshiepushki(self) -> None:
        """Test Case 3: 'крупнокалиберный' → bolshiepushki."""
        scorer = ChannelScorer()
        query = "крупнокалиберный"
        channel = {
            "username": "bolshiepushki",
            "title": "Крупнокалиберный Переполох",
            "description": "Секретный канал...",
        }
        score = scorer.score(query, channel)
        assert score >= 0.6  # Should match title prefix/token

    def test_score_returns_float(self) -> None:
        """Test score returns float between 0 and 1."""
        scorer = ChannelScorer()
        query = "test"
        channel = {
            "username": "test",
            "title": "Test",
            "description": "",
        }
        score = scorer.score(query, channel)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
