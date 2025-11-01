"""Configuration for MCP-aware agent parsing and stages.

Exposes environment-driven settings with sensible defaults.
"""

from __future__ import annotations

import os
from typing import Any, Dict


def _bool_from_env(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y"}


def _int_from_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float_from_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


# Parser settings
PARSER_STRICT_MODE: bool = _bool_from_env("PARSER_STRICT_MODE", False)
PARSER_MAX_ATTEMPTS: int = _int_from_env("PARSER_MAX_ATTEMPTS", 3)


# Agent stage settings
AGENT_CONFIG: Dict[str, Any] = {
    "decision_temperature": _float_from_env("AGENT_DECISION_TEMPERATURE", 0.2),
    "decision_max_tokens": _int_from_env("AGENT_DECISION_MAX_TOKENS", 256),
    "formatting_temperature": _float_from_env("AGENT_FORMATTING_TEMPERATURE", 0.7),
    "formatting_max_tokens": _int_from_env("AGENT_FORMATTING_MAX_TOKENS", 1024),
}


