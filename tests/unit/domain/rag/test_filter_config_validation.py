"""Tests for FilterConfig value object."""

import pytest

from src.domain.rag import FilterConfig


def test_filter_config_defaults_are_valid() -> None:
    """Ensure default configuration passes validation."""
    config = FilterConfig()

    assert config.score_threshold == pytest.approx(0.35)
    assert config.top_k == 5
    assert config.reranker_enabled is False
    assert config.reranker_strategy == "off"


@pytest.mark.parametrize("threshold", (-0.1, 1.1))
def test_filter_config_invalid_threshold_raises(threshold: float) -> None:
    """Validation should reject thresholds outside [0.0, 1.0]."""
    with pytest.raises(ValueError, match="score_threshold"):
        FilterConfig(score_threshold=threshold)


def test_filter_config_invalid_top_k_raises() -> None:
    """Validation should reject top_k values below one."""
    with pytest.raises(ValueError, match="top_k"):
        FilterConfig(top_k=0)


def test_filter_config_invalid_strategy_raises() -> None:
    """Validation should reject unsupported reranker strategies."""
    with pytest.raises(ValueError, match="reranker_strategy"):
        FilterConfig(reranker_strategy="bm25")  # type: ignore[arg-type]


def test_filter_config_requires_flag_for_strategy() -> None:
    """Enabling strategy requires reranker_enabled flag."""
    with pytest.raises(ValueError, match="requires reranker_enabled"):
        FilterConfig(reranker_strategy="llm", reranker_enabled=False)


def test_filter_config_allows_enabled_strategy() -> None:
    """Configuration is valid when strategy flag enabled."""
    config = FilterConfig(
        reranker_enabled=True,
        reranker_strategy="llm",
        score_threshold=0.3,
        top_k=3,
    )

    assert config.reranker_enabled is True
    assert config.reranker_strategy == "llm"


def test_filter_config_factory_enables_reranking() -> None:
    """Factory helper should configure reranking safely."""
    config = FilterConfig.with_reranking(
        score_threshold=0.25,
        top_k=4,
        strategy="llm",
    )

    assert config.reranker_enabled is True
    assert config.reranker_strategy == "llm"
    assert config.score_threshold == pytest.approx(0.25)
    assert config.top_k == 4
