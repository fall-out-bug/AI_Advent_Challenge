"""Unit tests for ReviewConfig and builder/preset utilities."""

from __future__ import annotations

import pytest
from multipass_reviewer.application.config import (
    ReviewConfig,
    ReviewConfigBuilder,
    ReviewConfigPresets,
)


def test_review_config_defaults() -> None:
    """Defaults should enable core passes and Python checker."""
    config = ReviewConfig()
    assert config.enable_architecture_pass is True
    assert config.enable_component_pass is True
    assert config.enable_synthesis_pass is True
    assert config.language_checkers == ["python"]
    assert config.static_analysis == []
    assert config.framework_checkers == []
    assert config.mlops_checkers == []
    assert config.data_checkers == []
    assert config.enable_haiku is False
    assert config.token_budget == 12000


@pytest.mark.parametrize(
    "preset,expected",  # type: ignore[type-arg]
    [
        (
            ReviewConfigPresets.python_lint_only(),
            {
                "language_checkers": ["python"],
                "static_analysis": ["linter", "type_checker"],
                "framework_checkers": [],
                "enable_haiku": False,
            },
        ),
        (
            ReviewConfigPresets.spark_airflow(),
            {
                "language_checkers": ["python"],
                "framework_checkers": ["spark", "airflow"],
                "data_checkers": ["schema", "quality", "storage"],
                "static_analysis": ["linter"],
                "enable_haiku": True,
            },
        ),
        (
            ReviewConfigPresets.mlops_full_stack(),
            {
                "language_checkers": ["python"],
                "mlops_checkers": ["model", "data", "pipeline"],
                "static_analysis": ["linter", "type_checker", "security"],
                "enable_haiku": True,
                "enable_log_analysis": True,
            },
        ),
    ],
)
def test_review_config_presets(preset, expected):  # type: ignore[no-untyped-def]
    """Presets should apply curated combinations."""
    for key, value in expected.items():
        assert getattr(preset, key) == value


def test_review_config_builder_complex() -> None:
    """Builder should combine multiple options with validation."""
    config = (
        ReviewConfigBuilder()
        .with_language("python")
        .with_language("go")
        .with_static_analysis(["linter", "formatter"])
        .with_framework("spark")
        .with_mlops(["model", "pipeline"])
        .enable_haiku()
        .enable_log_analysis()
        .set_token_budget(16000)
        .build()
    )

    assert config.language_checkers == ["python", "go"]
    assert config.static_analysis == ["linter", "formatter"]
    assert config.framework_checkers == ["spark"]
    assert config.mlops_checkers == ["model", "pipeline"]
    assert config.enable_haiku is True
    assert config.enable_log_analysis is True
    assert config.token_budget == 16000


def test_review_config_builder_validation() -> None:
    """Builder should reject duplicate or unsupported entries."""
    builder = ReviewConfigBuilder()
    builder.with_language("python")
    builder.with_language("python")  # duplicate ignored
    builder.with_static_analysis(["linter", "linter"])  # duplicate ignored

    config = builder.build()
    assert config.language_checkers == ["python"]
    assert config.static_analysis == ["linter"]


def test_review_config_invalid_token_budget() -> None:
    """Token budget must be positive."""
    with pytest.raises(ValueError):
        ReviewConfig(token_budget=0)


def test_review_config_invalid_checker_name() -> None:
    """Unsupported checker names should raise ValueError."""
    with pytest.raises(ValueError):
        ReviewConfig(language_checkers=["unknown"])
