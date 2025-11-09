"""Configuration module for shared SDK."""

from .constants import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TEMPERATURE_CLAMP,
    DEFAULT_TIMEOUT,
    MAX_TEMPERATURE,
    MAX_TOKENS_LIMIT,
    MIN_TEMPERATURE,
    MIN_TOKENS,
    QUICK_TIMEOUT,
    TEST_MAX_TOKENS,
    TEST_TIMEOUT,
)
from .models import (
    LOCAL_MODELS,
    MODEL_CONFIGS,
    MODEL_PORTS,
    ModelName,
    ModelPort,
    ModelType,
    get_local_models,
    get_model_config,
    get_model_port,
    is_local_model,
)

# Agent configurations will be imported when available
try:
    from .agents import (
        AGENT_CONFIGS,
        DEFAULT_GENERATOR_CONFIG,
        DEFAULT_REVIEWER_CONFIG,
        MODEL_AGENT_COMPATIBILITY,
        AgentConfig,
        CodeGeneratorConfig,
        CodeReviewerConfig,
        get_agent_config,
        get_compatible_models,
        get_model_config_for_agent,
        get_prompt_template,
        get_recommended_models,
        is_model_recommended_for_agent,
    )

    __all__ = [
        # Model configurations
        "ModelType",
        "ModelName",
        "ModelPort",
        "MODEL_CONFIGS",
        "MODEL_PORTS",
        "LOCAL_MODELS",
        "get_model_config",
        "get_local_models",
        "get_model_port",
        "is_local_model",
        # Constants
        "DEFAULT_TIMEOUT",
        "QUICK_TIMEOUT",
        "TEST_TIMEOUT",
        "DEFAULT_MAX_TOKENS",
        "DEFAULT_TEMPERATURE",
        "TEST_MAX_TOKENS",
        "MIN_TEMPERATURE",
        "MAX_TEMPERATURE",
        "DEFAULT_TEMPERATURE_CLAMP",
        "MIN_TOKENS",
        "MAX_TOKENS_LIMIT",
        # Agent configurations
        "AgentConfig",
        "CodeGeneratorConfig",
        "CodeReviewerConfig",
        "DEFAULT_GENERATOR_CONFIG",
        "DEFAULT_REVIEWER_CONFIG",
        "AGENT_CONFIGS",
        "MODEL_AGENT_COMPATIBILITY",
        "get_agent_config",
        "get_model_config_for_agent",
        "is_model_recommended_for_agent",
        "get_compatible_models",
        "get_recommended_models",
        "get_prompt_template",
    ]
except ImportError:
    # Agent configurations not available (pre-phase 6)
    __all__ = [
        # Model configurations
        "ModelType",
        "ModelName",
        "ModelPort",
        "MODEL_CONFIGS",
        "MODEL_PORTS",
        "LOCAL_MODELS",
        "get_model_config",
        "get_local_models",
        "get_model_port",
        "is_local_model",
        # Constants
        "DEFAULT_TIMEOUT",
        "QUICK_TIMEOUT",
        "TEST_TIMEOUT",
        "DEFAULT_MAX_TOKENS",
        "DEFAULT_TEMPERATURE",
        "TEST_MAX_TOKENS",
        "MIN_TEMPERATURE",
        "MAX_TEMPERATURE",
        "DEFAULT_TEMPERATURE_CLAMP",
        "MIN_TOKENS",
        "MAX_TOKENS_LIMIT",
    ]
