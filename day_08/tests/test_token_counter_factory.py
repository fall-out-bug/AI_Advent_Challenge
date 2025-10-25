"""
Tests for TokenCounterFactory.
"""

import pytest

from core.factories import TokenCounterFactory
from core.token_analyzer import LimitProfile
from tests.mocks import MockConfiguration


class TestTokenCounterFactory:
    """Test cases for TokenCounterFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = MockConfiguration()

    def test_create_simple_with_config(self):
        """Test creating simple token counter with config."""
        counter = TokenCounterFactory.create_simple(
            config=self.mock_config, limit_profile=LimitProfile.THEORETICAL
        )

        assert counter.limit_profile == LimitProfile.THEORETICAL
        assert counter.config == self.mock_config

    def test_create_simple_without_config(self):
        """Test creating simple token counter without config."""
        counter = TokenCounterFactory.create_simple()

        assert counter.limit_profile == LimitProfile.PRACTICAL
        assert counter.config is None

    def test_create_accurate(self):
        """Test creating accurate token counter."""
        counter = TokenCounterFactory.create_accurate()

        assert counter is not None
        # AccurateTokenCounter doesn't have limit_profile attribute
        assert not hasattr(counter, "limit_profile")

    def test_create_hybrid_simple_mode(self):
        """Test creating hybrid token counter in simple mode."""
        counter = TokenCounterFactory.create_hybrid(
            mode="simple",
            config=self.mock_config,
            limit_profile=LimitProfile.THEORETICAL,
        )

        assert counter.mode == "simple"
        # In simple mode, the limit profile is stored in the underlying counter
        assert counter._counter.limit_profile == LimitProfile.THEORETICAL
        assert counter._counter.config == self.mock_config

    def test_create_hybrid_accurate_mode(self):
        """Test creating hybrid token counter in accurate mode."""
        counter = TokenCounterFactory.create_hybrid(
            mode="accurate",
            config=self.mock_config,
            limit_profile=LimitProfile.THEORETICAL,
        )

        assert counter.mode == "accurate"
        assert counter._limit_profile == LimitProfile.THEORETICAL
        assert counter._config == self.mock_config

    def test_create_hybrid_invalid_mode(self):
        """Test creating hybrid token counter with invalid mode."""
        with pytest.raises(ValueError, match="Unknown mode: invalid"):
            TokenCounterFactory.create_hybrid(mode="invalid")

    def test_create_from_config_simple(self):
        """Test creating token counter from config in simple mode."""
        counter = TokenCounterFactory.create_from_config(
            config=self.mock_config,
            mode="simple",
            limit_profile=LimitProfile.THEORETICAL,
        )

        assert isinstance(counter, TokenCounterFactory.create_simple().__class__)
        assert counter.limit_profile == LimitProfile.THEORETICAL
        assert counter.config == self.mock_config

    def test_create_from_config_accurate(self):
        """Test creating token counter from config in accurate mode."""
        counter = TokenCounterFactory.create_from_config(
            config=self.mock_config, mode="accurate"
        )

        assert isinstance(counter, TokenCounterFactory.create_accurate().__class__)

    def test_create_from_config_hybrid(self):
        """Test creating token counter from config in hybrid mode."""
        counter = TokenCounterFactory.create_from_config(
            config=self.mock_config,
            mode="hybrid",
            limit_profile=LimitProfile.THEORETICAL,
        )

        assert isinstance(counter, TokenCounterFactory.create_hybrid().__class__)
        assert counter.mode == "simple"  # Hybrid defaults to simple mode

    def test_create_from_config_invalid_mode(self):
        """Test creating token counter from config with invalid mode."""
        with pytest.raises(ValueError, match="Unsupported mode: invalid"):
            TokenCounterFactory.create_from_config(
                config=self.mock_config, mode="invalid"
            )

    def test_factory_methods_return_correct_types(self):
        """Test that factory methods return correct types."""
        simple = TokenCounterFactory.create_simple()
        accurate = TokenCounterFactory.create_accurate()
        hybrid = TokenCounterFactory.create_hybrid()

        assert hasattr(simple, "count_tokens")
        assert hasattr(accurate, "count_tokens")
        assert hasattr(hybrid, "count_tokens")

        # Test that they can count tokens
        result = simple.count_tokens("test")
        assert result.count > 0

        result = hybrid.count_tokens("test")
        assert result.count > 0
