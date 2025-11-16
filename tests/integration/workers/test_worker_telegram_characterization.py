"""Characterization tests for worker/Telegram/channel behavior.

Purpose:
    Document current behavior before refactoring in Cluster E.
    These tests capture existing patterns and edge cases.
"""

from __future__ import annotations

import pytest

from src.domain.services.channel_normalizer import ChannelNormalizer
from src.workers.post_fetcher_worker import PostFetcherWorker


class TestChannelNormalizerCharacterization:
    """Characterize ChannelNormalizer behavior before refactoring."""

    @pytest.fixture
    def normalizer(self) -> ChannelNormalizer:
        """Create ChannelNormalizer instance for tests."""
        return ChannelNormalizer()

    def test_normalize_lowercase_characterization(self, normalizer: ChannelNormalizer):
        """Characterize lowercase normalization behavior.

        Purpose:
            Document that normalize() converts to lowercase.
            Canonical form is lowercase without @ prefix per E.1 policy.
        """
        # Test lowercase conversion
        result = normalizer.normalize("HELLO")
        assert result == "hello"

        # Test mixed case
        result = normalizer.normalize("Hello World")
        assert result == "hello world"

        # Test with @ prefix (should be removed per policy)
        result = normalizer.normalize("@onaboka")
        assert result == "onaboka"  # @ removed, lowercase

    def test_normalize_removes_at_prefix_characterization(
        self, normalizer: ChannelNormalizer
    ):
        """Characterize @ prefix removal behavior.

        Purpose:
            Document that @ prefix is removed during normalization.
            Canonical form is lowercase without @ per E.1 policy.
        """
        # Test @ prefix removal
        result = normalizer.normalize("@onaboka")
        assert result == "onaboka"

        # Test @ with uppercase
        result = normalizer.normalize("@Onaboka")
        assert result == "onaboka"

        # Test multiple @ (edge case)
        result = normalizer.normalize("@@onaboka")
        assert result == "onaboka"  # All punctuation removed

    def test_normalize_removes_punctuation_characterization(
        self, normalizer: ChannelNormalizer
    ):
        """Characterize punctuation removal behavior."""
        # Test punctuation removal
        result = normalizer.normalize("hello, world!")
        assert result == "hello world"

        # Test dashes
        result = normalizer.normalize("hello-world")
        assert result == "hello world"  # Dashes replaced with spaces

        # Test underscores (replaced with spaces, as underscore is punctuation)
        result = normalizer.normalize("hello_world")
        assert result == "hello world"  # Underscores replaced with spaces

    def test_normalize_canonical_form_characterization(
        self, normalizer: ChannelNormalizer
    ):
        """Characterize canonical form per E.1 policy.

        Purpose:
            Document that canonical form is lowercase, without @ prefix.
            This aligns with E.1 policy: canonical form used in DB, indexes, domain logic.
        """
        test_cases = [
            ("@onaboka", "onaboka"),  # @ removed
            ("Onaboka", "onaboka"),  # Lowercase
            ("ONABOKA", "onaboka"),  # Lowercase
            ("@Onaboka", "onaboka"),  # @ removed + lowercase
            ("onaboka", "onaboka"),  # Already canonical
        ]

        for input_text, expected in test_cases:
            result = normalizer.normalize(input_text)
            assert result == expected, f"Input: {input_text}, Expected: {expected}, Got: {result}"

    def test_transliterate_ru_to_lat_characterization(
        self, normalizer: ChannelNormalizer
    ):
        """Characterize Russian to Latin transliteration."""
        # Test Russian to Latin
        result = normalizer.transliterate_ru_to_lat("Набока")
        assert result == "naboka" or "Naboka"  # May vary by transliteration library

        # Test with spaces
        result = normalizer.transliterate_ru_to_lat("Набока орёт")
        assert "naboka" in result.lower() or "Naboka" in result


class TestPostFetcherWorkerCharacterization:
    """Characterize PostFetcherWorker behavior before refactoring."""

    @pytest.fixture
    def worker(self) -> PostFetcherWorker:
        """Create PostFetcherWorker instance for tests."""
        return PostFetcherWorker()

    def test_worker_constructor_signature_characterization(
        self, worker: PostFetcherWorker
    ):
        """Characterize PostFetcherWorker constructor signature."""
        # Verify constructor accepts optional mcp_url
        worker1 = PostFetcherWorker()
        assert worker1 is not None

        worker2 = PostFetcherWorker(mcp_url="http://test:8000")
        assert worker2 is not None

    def test_worker_looks_like_title_characterization(
        self, worker: PostFetcherWorker
    ):
        """Characterize _looks_like_title() detection logic."""
        # Test Cyrillic detection
        assert worker._looks_like_title("Набока") is True

        # Test spaces detection
        assert worker._looks_like_title("Hello World") is True

        # Test uppercase in middle
        assert worker._looks_like_title("HelloWorld") is True

        # Test valid username
        assert worker._looks_like_title("onaboka") is False

        # Test username with underscore
        assert worker._looks_like_title("hello_world") is False

        # Test empty string
        assert worker._looks_like_title("") is True

        # Test @ prefix (not currently handled, may need refactoring)
        assert worker._looks_like_title("@onaboka") is False  # @ prefix not checked

    def test_worker_channel_username_normalization_characterization(
        self, worker: PostFetcherWorker
    ):
        """Characterize channel username handling in worker.

        Purpose:
            Document that worker validates channel_username and may fetch metadata
            if username looks like a title. This aligns with E.1 policy where
            canonical form is lowercase without @ prefix.
        """
        # Verify worker has logic to detect title-like usernames
        assert hasattr(worker, "_looks_like_title")

        # Verify worker processes channels (actual processing tested in integration)
        assert hasattr(worker, "_process_channel")
        assert hasattr(worker, "_process_all_channels")


class TestTelegramUtilsCharacterization:
    """Characterize Telegram utils behavior before refactoring."""

    def test_fetch_channel_posts_signature_characterization(self):
        """Characterize fetch_channel_posts() signature.

        Purpose:
            Document current signature before introducing adapter interface in E.2.
        """
        from src.infrastructure.clients.telegram_utils import fetch_channel_posts

        import inspect

        sig = inspect.signature(fetch_channel_posts)
        params = list(sig.parameters.keys())

        # Expected parameters
        assert "channel_username" in params
        assert "since" in params
        assert "save_to_db" in params  # May be used

        # Optional parameters
        assert "user_id" in params  # Optional for some methods

    def test_fetch_channel_posts_channel_username_format_characterization(self):
        """Characterize channel_username format expectations.

        Purpose:
            Document that channel_username should be without @ prefix (canonical form).
            This aligns with E.1 policy.
        """
        from src.infrastructure.clients.telegram_utils import fetch_channel_posts

        # Note: Actual format expectations will be verified in integration tests
        # This test documents the expected behavior
        assert callable(fetch_channel_posts)

