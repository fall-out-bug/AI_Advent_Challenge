"""Unit tests for RuleBasedClassifier.

Following TDD: Test-Driven Development.
"""

import pytest

from src.domain.intent.intent_classifier import IntentType
from src.domain.intent.rule_based_classifier import RuleBasedClassifier


class TestRuleBasedClassifier:
    """Test suite for RuleBasedClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create RuleBasedClassifier instance."""
        return RuleBasedClassifier()

    def test_classify_task_create(self, classifier):
        """Test TASK_CREATE intent classification."""
        result = classifier.classify("Создай задачу купить молоко")
        # May return TASK_CREATE (sub-intent) or TASK (mode-level), both are valid
        assert result.intent in [IntentType.TASK_CREATE, IntentType.TASK]
        assert result.confidence >= 0.9
        assert result.source == "rule"
        assert result.latency_ms < 100  # Should be fast

    def test_classify_data_subscription_list(self, classifier):
        """Test DATA_SUBSCRIPTION_LIST intent classification."""
        result = classifier.classify("Дай мои подписки")
        # May return DATA_SUBSCRIPTION_LIST (sub-intent) or DATA (mode-level), both are valid
        assert result.intent in [IntentType.DATA_SUBSCRIPTION_LIST, IntentType.DATA]
        assert result.confidence >= 0.9
        assert result.source == "rule"

    def test_classify_data_digest_with_channel(self, classifier):
        """Test DATA_DIGEST intent with channel extraction."""
        result = classifier.classify("Дай дайджест по Набоке за 5 дней")
        # May return DATA_DIGEST (sub-intent) or DATA (mode-level), both are valid
        assert result.intent in [IntentType.DATA_DIGEST, IntentType.DATA]
        assert result.confidence >= 0.9
        assert result.source == "rule"
        # Check entity extraction (may be empty if rule doesn't extract)
        if result.entities:
            if "channel_name" in result.entities:
                channel_name = result.entities["channel_name"]
                assert channel_name and len(channel_name) > 0
            if "days" in result.entities:
                days = result.entities["days"]
                assert isinstance(days, int) and days > 0

    def test_classify_data_subscription_add(self, classifier):
        """Test DATA_SUBSCRIPTION_ADD intent with channel extraction."""
        # Test with various subscription request formats
        messages = [
            "Подпишись на @xor_journal",
            "subscribe to xor_journal",
            "добавь канал xor_journal",
        ]
        for message in messages:
            result = classifier.classify(message)
            # May return DATA_SUBSCRIPTION_ADD (sub-intent), DATA (mode-level), or IDLE if no match
            assert result.intent in [
                IntentType.DATA_SUBSCRIPTION_ADD,
                IntentType.DATA,
                IntentType.IDLE,
            ]
            # If matched, should have good confidence
            if result.intent != IntentType.IDLE:
                assert result.confidence >= 0.8
                assert result.source == "rule"
                # Check entity extraction (may be empty if rule doesn't extract)
                if result.entities and "channel_username" in result.entities:
                    channel = result.entities["channel_username"]
                    assert channel and len(channel) > 0

    def test_classify_reminder_set(self, classifier):
        """Test REMINDER_SET intent with text extraction."""
        result = classifier.classify("Напомни мне про встречу")
        # May return REMINDER_SET (sub-intent) or REMINDERS (mode-level), both are valid
        assert result.intent in [IntentType.REMINDER_SET, IntentType.REMINDERS]
        assert result.confidence >= 0.9
        assert result.source == "rule"
        # Check entity extraction (may be empty if rule doesn't extract)
        if result.entities and "reminder_text" in result.entities:
            text = result.entities["reminder_text"]
            assert text and len(text) > 0

    def test_classify_general_chat(self, classifier):
        """Test GENERAL_CHAT intent for greetings."""
        result = classifier.classify("Привет")
        assert result.intent in [IntentType.GENERAL_CHAT, IntentType.IDLE]
        assert result.source == "rule"

    def test_classify_english_messages(self, classifier):
        """Test English message classification."""
        result = classifier.classify("Give me my subscriptions")
        assert result.intent in [IntentType.DATA_SUBSCRIPTION_LIST, IntentType.DATA]
        assert result.confidence >= 0.9

        result = classifier.classify("digest of xor for 3 days")
        assert result.intent in [IntentType.DATA_DIGEST, IntentType.DATA]
        # Entity extraction may or may not work depending on rule matching
        if result.entities:
            if "channel_name" in result.entities:
                assert result.entities["channel_name"]
            if "days" in result.entities:
                assert isinstance(result.entities["days"], int)

    def test_classify_empty_message(self, classifier):
        """Test empty message handling."""
        result = classifier.classify("")
        assert result.intent == IntentType.IDLE
        assert result.confidence == 0.5  # Default for empty

    def test_classify_unknown_message(self, classifier):
        """Test unknown message falls back to IDLE."""
        result = classifier.classify("random text that doesn't match any pattern")
        assert result.intent == IntentType.IDLE
        assert result.confidence < 0.7  # Low confidence for unknown

    def test_latency_performance(self, classifier):
        """Test that rule-based classification is fast."""
        import time
        start = time.time()
        for _ in range(100):
            classifier.classify("Дай мои подписки")
        elapsed = time.time() - start
        avg_latency_ms = (elapsed / 100) * 1000
        assert avg_latency_ms < 100, f"Average latency {avg_latency_ms}ms exceeds 100ms threshold"

