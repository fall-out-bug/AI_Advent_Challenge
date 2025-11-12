"""Configuration loader for RAG reranking pipeline."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, PositiveInt, field_validator


class RetrievalConfig(BaseModel):
    """Configuration for initial retrieval stage."""

    top_k: PositiveInt = Field(default=5, description="Maximum number of chunks.")
    score_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Similarity score threshold."
    )
    vector_search_headroom_multiplier: PositiveInt = Field(
        default=2, description="Multiplier for pre-filter vector search."
    )


class RerankerLLMConfig(BaseModel):
    """Configuration for LLM-based reranker."""

    model: str = Field(default="mistral:7b-instruct")
    temperature: float = Field(default=0.5, ge=0.0, le=1.0)
    max_tokens: PositiveInt = Field(default=256)
    timeout_seconds: PositiveInt = Field(default=3)
    temperature_override_env: str | None = Field(default="RAG_RERANK_TEMPERATURE")


class RerankerCrossEncoderConfig(BaseModel):
    """Configuration for cross-encoder reranker (future)."""

    model_name: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Sentence-transformers cross-encoder model.",
    )
    batch_size: PositiveInt = Field(default=8)


class RerankerConfig(BaseModel):
    """Configuration for reranking stage."""

    enabled: bool = False
    strategy: str = Field(default="off")
    llm: RerankerLLMConfig = Field(default_factory=RerankerLLMConfig)
    cross_encoder: RerankerCrossEncoderConfig = Field(
        default_factory=RerankerCrossEncoderConfig
    )

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        allowed = {"off", "llm", "cross_encoder"}
        if value not in allowed:
            raise ValueError(f"strategy must be one of {allowed}")
        return value

    @field_validator("enabled")
    @classmethod
    def validate_enabled(cls, value: bool, info) -> bool:
        strategy = getattr(info, "data", {}).get("strategy", "off")
        if strategy != "off" and not value:
            raise ValueError("strategy != 'off' requires enabled=True")
        return value


class FeatureFlagsConfig(BaseModel):
    """Feature flag configuration."""

    enable_rag_plus_plus: bool = False


class RagRerankConfig(BaseModel):
    """Top-level configuration for RAG++ pipeline."""

    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    feature_flags: FeatureFlagsConfig = Field(default_factory=FeatureFlagsConfig)

    def with_overrides(
        self,
        *,
        score_threshold: float | None = None,
        top_k: int | None = None,
        reranker_enabled: bool | None = None,
        reranker_strategy: str | None = None,
    ) -> "RagRerankConfig":
        """Return new configuration with runtime overrides applied."""
        data = self.model_dump()
        if score_threshold is not None:
            data["retrieval"]["score_threshold"] = score_threshold
        if top_k is not None:
            data["retrieval"]["top_k"] = top_k
        if reranker_enabled is not None:
            data["reranker"]["enabled"] = reranker_enabled
        if reranker_strategy is not None:
            data["reranker"]["strategy"] = reranker_strategy
        return RagRerankConfig.model_validate(data)


def _config_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / "retrieval_rerank_config.yaml"


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _apply_env_overrides(data: dict) -> dict:
    retrieval = data.setdefault("retrieval", {})
    reranker = data.setdefault("reranker", {})
    feature_flags = data.setdefault("feature_flags", {})

    if env_threshold := os.getenv("RAG_SCORE_THRESHOLD"):
        try:
            retrieval["score_threshold"] = float(env_threshold)
        except ValueError as error:
            raise ValueError("RAG_SCORE_THRESHOLD must be a float.") from error

    if env_top_k := os.getenv("RAG_TOP_K"):
        try:
            retrieval["top_k"] = int(env_top_k)
        except ValueError as error:
            raise ValueError("RAG_TOP_K must be an integer.") from error

    if env_enabled := os.getenv("RAG_RERANKER_ENABLED"):
        reranker["enabled"] = env_enabled.lower() in {"1", "true", "yes"}

    if env_strategy := os.getenv("RAG_RERANKER_STRATEGY"):
        reranker["strategy"] = env_strategy

    llm = reranker.setdefault("llm", {})
    override_env_name = llm.get("temperature_override_env")
    env_name = override_env_name or "RAG_RERANK_TEMPERATURE"
    if env_name and (env_temperature := os.getenv(env_name)):
        try:
            llm["temperature"] = float(env_temperature)
        except ValueError as error:
            raise ValueError(f"{env_name} must be a float.") from error
    if env_timeout := os.getenv("RAG_RERANK_TIMEOUT"):
        try:
            llm["timeout_seconds"] = int(env_timeout)
        except ValueError as error:
            raise ValueError("RAG_RERANK_TIMEOUT must be an integer.") from error

    if env_flag := os.getenv("RAG_PLUS_PLUS_ENABLED"):
        feature_flags["enable_rag_plus_plus"] = env_flag.lower() in {"1", "true", "yes"}

    return data


@lru_cache(maxsize=1)
def load_rag_rerank_config(path: Path | None = None) -> RagRerankConfig:
    """Load RAG rerank configuration from YAML with env overrides."""
    config_path = path or _config_path()
    data = _apply_env_overrides(_load_yaml(config_path))
    return RagRerankConfig.model_validate(data)


__all__ = ["RagRerankConfig", "RetrievalConfig", "RerankerConfig", "load_rag_rerank_config"]
