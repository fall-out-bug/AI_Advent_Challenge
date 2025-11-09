"""Review configuration data structures and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

VALID_LANGUAGES = {"python", "go", "java", "typescript"}
VALID_STATIC_ANALYSIS = {"linter", "type_checker", "formatter", "security"}
VALID_FRAMEWORKS = {"spark", "airflow", "fastapi", "django"}
VALID_MLOPS = {"model", "data", "pipeline", "experiment", "deployment"}
VALID_DATA = {"schema", "quality", "transform", "storage", "warehouse"}


@dataclass(slots=True)
class ReviewConfig:
    """Configuration object describing passes and checker selections."""

    enable_architecture_pass: bool = True
    enable_component_pass: bool = True
    enable_synthesis_pass: bool = True

    language_checkers: List[str] = field(default_factory=lambda: ["python"])
    static_analysis: List[str] = field(default_factory=list)
    framework_checkers: List[str] = field(default_factory=list)
    mlops_checkers: List[str] = field(default_factory=list)
    data_checkers: List[str] = field(default_factory=list)

    enable_haiku: bool = False
    enable_log_analysis: bool = False
    enable_metrics_validation: bool = False

    checker_config: dict[str, dict[str, Any]] = field(default_factory=dict)
    token_budget: int = 12000

    def __post_init__(self) -> None:
        """Validate configuration fields."""
        if self.token_budget <= 0:
            raise ValueError("token_budget must be positive")
        self.language_checkers = self._validate_list(
            self.language_checkers, VALID_LANGUAGES, "language_checkers"
        )
        self.static_analysis = self._validate_list(
            self.static_analysis, VALID_STATIC_ANALYSIS, "static_analysis"
        )
        self.framework_checkers = self._validate_list(
            self.framework_checkers, VALID_FRAMEWORKS, "framework_checkers"
        )
        self.mlops_checkers = self._validate_list(
            self.mlops_checkers, VALID_MLOPS, "mlops_checkers"
        )
        self.data_checkers = self._validate_list(
            self.data_checkers, VALID_DATA, "data_checkers"
        )

    @staticmethod
    def _validate_list(
        values: List[str], allowed: set[str], field_name: str
    ) -> List[str]:
        """Ensure values are unique and part of the allowed set."""
        cleaned: List[str] = []
        for value in values:
            if value not in allowed:
                raise ValueError(f"Unsupported value '{value}' for {field_name}")
            if value not in cleaned:
                cleaned.append(value)
        return cleaned


class ReviewConfigPresets:
    """Factory for opinionated configuration presets."""

    @staticmethod
    def python_lint_only() -> ReviewConfig:
        return ReviewConfig(
            language_checkers=["python"],
            static_analysis=["linter", "type_checker"],
            enable_haiku=False,
        )

    @staticmethod
    def spark_airflow() -> ReviewConfig:
        return ReviewConfig(
            language_checkers=["python"],
            framework_checkers=["spark", "airflow"],
            data_checkers=["schema", "quality", "storage"],
            static_analysis=["linter"],
            enable_haiku=True,
        )

    @staticmethod
    def mlops_full_stack() -> ReviewConfig:
        return ReviewConfig(
            language_checkers=["python"],
            mlops_checkers=["model", "data", "pipeline"],
            static_analysis=["linter", "type_checker", "security"],
            enable_haiku=True,
            enable_log_analysis=True,
        )


class ReviewConfigBuilder:
    """Fluent builder for complex review configurations."""

    def __init__(self) -> None:
        self._config = ReviewConfig()

    def with_language(self, language: str) -> "ReviewConfigBuilder":
        if (
            language in VALID_LANGUAGES
            and language not in self._config.language_checkers
        ):
            self._config.language_checkers.append(language)
        return self

    def with_static_analysis(self, checks: List[str]) -> "ReviewConfigBuilder":
        for check in checks:
            if (
                check in VALID_STATIC_ANALYSIS
                and check not in self._config.static_analysis
            ):
                self._config.static_analysis.append(check)
        return self

    def with_framework(self, framework: str) -> "ReviewConfigBuilder":
        if (
            framework in VALID_FRAMEWORKS
            and framework not in self._config.framework_checkers
        ):
            self._config.framework_checkers.append(framework)
        return self

    def with_mlops(self, checkers: List[str]) -> "ReviewConfigBuilder":
        for checker in checkers:
            if checker in VALID_MLOPS and checker not in self._config.mlops_checkers:
                self._config.mlops_checkers.append(checker)
        return self

    def with_data(self, checkers: List[str]) -> "ReviewConfigBuilder":
        for checker in checkers:
            if checker in VALID_DATA and checker not in self._config.data_checkers:
                self._config.data_checkers.append(checker)
        return self

    def enable_haiku(self, value: bool = True) -> "ReviewConfigBuilder":
        self._config.enable_haiku = value
        return self

    def enable_log_analysis(self, value: bool = True) -> "ReviewConfigBuilder":
        self._config.enable_log_analysis = value
        return self

    def enable_metrics_validation(self, value: bool = True) -> "ReviewConfigBuilder":
        self._config.enable_metrics_validation = value
        return self

    def set_token_budget(self, token_budget: int) -> "ReviewConfigBuilder":
        if token_budget <= 0:
            raise ValueError("token_budget must be positive")
        self._config.token_budget = token_budget
        return self

    def build(self) -> ReviewConfig:
        data: dict[str, Any] = {
            "enable_architecture_pass": self._config.enable_architecture_pass,
            "enable_component_pass": self._config.enable_component_pass,
            "enable_synthesis_pass": self._config.enable_synthesis_pass,
            "language_checkers": list(self._config.language_checkers),
            "static_analysis": list(self._config.static_analysis),
            "framework_checkers": list(self._config.framework_checkers),
            "mlops_checkers": list(self._config.mlops_checkers),
            "data_checkers": list(self._config.data_checkers),
            "enable_haiku": self._config.enable_haiku,
            "enable_log_analysis": self._config.enable_log_analysis,
            "enable_metrics_validation": self._config.enable_metrics_validation,
            "checker_config": dict(self._config.checker_config),
            "token_budget": self._config.token_budget,
        }
        return ReviewConfig(**data)
