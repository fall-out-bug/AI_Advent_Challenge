"""Integration tests for channel resolution cases.

Following TDD: tests written first before implementation.
Tests the three real-world cases from the plan.
"""

from __future__ import annotations

import pytest

from src.domain.services.channel_normalizer import ChannelNormalizer
from src.domain.services.channel_scorer import ChannelScorer


class TestChannelResolutionCases:
    """Integration tests for real-world channel resolution cases."""

    @pytest.fixture
    def normalizer(self) -> ChannelNormalizer:
        """Create ChannelNormalizer instance."""
        return ChannelNormalizer()

    @pytest.fixture
    def scorer(self) -> ChannelScorer:
        """Create ChannelScorer instance."""
        return ChannelScorer()

    def test_case_1_onaboka_subscription(self, scorer: ChannelScorer) -> None:
        """Test Case 1: onaboka / 'Набока' → should match onaboka."""
        # User query
        query = "Набока"
        
        # Channel from subscriptions
        channel = {
            "username": "onaboka",
            "title": "Набока орёт в борщ",
            "description": (
                "Chief Mandezh Officer. "
                "Леся Набока — хулиганка, ПЗРК, HRD «КамшотБанк», "
                "кофаундер Карьерного Цеха. YouTube-подкаст «Два стула». "
                "Амбассадор женщин, криптонит для долбоебов. "
                "🖊 Связь @ask_naboka_bot"
            ),
        }
        
        score = scorer.score(query, channel)
        assert score >= 0.6, f"Score {score} should be >= 0.6 for onaboka match"

    def test_case_2_xor_journal_subscription(self, scorer: ChannelScorer) -> None:
        """Test Case 2: xor_journal / 'XOR' → should match xor_journal."""
        # User query
        query = "XOR"
        
        # Channel from subscriptions
        channel = {
            "username": "xor_journal",
            "title": "XOR",
            "description": (
                "Это журнал о программировании и технологиях. "
                "Здесь ты найдешь все самое интересное и свежее из мира IT. "
                "Редакция: @xorjournal_bot "
                "Сотрудничество: @todaycast "
                "РКН: https://clck.ru/3FjUWa"
            ),
        }
        
        score = scorer.score(query, channel)
        assert score >= 0.8, f"Score {score} should be >= 0.8 for XOR match"

    def test_case_3_bolshiepushki_discovery(
        self, scorer: ChannelScorer
    ) -> None:
        """Test Case 3: 'крупнокалиберный' → should match bolshiepushki."""
        # User query for subscription
        query = "крупнокалиберный"
        
        # Channel found via Telegram search
        channel = {
            "username": "bolshiepushki",
            "title": "Крупнокалиберный Переполох",
            "description": (
                "Секретный канал https://t.me/Krupnokaliberniy_bot "
                "https://knd.gov.ru/license?id=6757f00935130d723645f884&registryType=bloggersPermission "
                "Реклама @reklamakomandante "
                "Поддержать https://pay.cloudtips.ru/p/9f351cb9 "
                "Бот для связи @bolshiepushki_helpme_bot"
            ),
        }
        
        score = scorer.score(query, channel)
        assert score >= 0.6, f"Score {score} should be >= 0.6 for bolshiepushki match"

    def test_case_1_normalization(self, normalizer: ChannelNormalizer) -> None:
        """Test Case 1 normalization works correctly."""
        query = "Набока"
        normalized = normalizer.normalize(query)
        assert "набока" in normalized.lower()
        
        # Should transliterate to Latin
        transliterated = normalizer.transliterate_ru_to_lat("Набока")
        assert "naboka" in transliterated.lower()

    def test_case_3_transliteration(self, normalizer: ChannelNormalizer) -> None:
        """Test Case 3 transliteration works correctly."""
        query = "крупнокалиберный"
        transliterated = normalizer.transliterate_ru_to_lat(query)
        assert "krupnokaliberny" in transliterated.lower()

    def test_negative_case_low_score(self, scorer: ChannelScorer) -> None:
        """Test that unrelated channels get low scores."""
        query = "Набока"
        unrelated_channel = {
            "username": "completely_different",
            "title": "Completely Different Title",
            "description": "Some unrelated description",
        }
        
        score = scorer.score(query, unrelated_channel)
        assert score < 0.4, f"Score {score} should be < 0.4 for unrelated channel"

    def test_multiple_candidates_ranking(self, scorer: ChannelScorer) -> None:
        """Test that correct channel ranks highest among multiple candidates."""
        query = "Набока"
        
        candidates = [
            {
                "username": "onaboka",
                "title": "Набока орёт в борщ",
                "description": "Леся Набока — хулиганка...",
            },
            {
                "username": "xor_journal",
                "title": "XOR",
                "description": "Это журнал о программировании...",
            },
            {
                "username": "bolshiepushki",
                "title": "Крупнокалиберный Переполох",
                "description": "Секретный канал...",
            },
        ]
        
        scores = [scorer.score(query, ch) for ch in candidates]
        
        # onaboka should have the highest score
        onaboka_score = scores[0]
        assert onaboka_score == max(scores), (
            f"onaboka should have highest score, got {scores}"
        )
        assert onaboka_score >= 0.6, f"onaboka score {onaboka_score} should be >= 0.6"

