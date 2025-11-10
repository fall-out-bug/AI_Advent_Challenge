"""
Agent-specific configurations for the SDK.

Following Python Zen: "Explicit is better than implicit"
and "Simple is better than complex".

This module provides:
- Agent-specific configurations (max_tokens, temperature)
- Model-agent compatibility matrix
- Default prompt templates
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    max_tokens: int = 2000
    temperature: float = 0.7
    max_retries: int = 3
    timeout: float = 600.0


@dataclass
class CodeGeneratorConfig(AgentConfig):
    """Configuration for code generator agent."""

    max_tokens: int = 4000  # More tokens for code generation
    temperature: float = 0.7  # Balanced creativity
    supported_languages: List[str] = None

    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = [
                "python",
                "javascript",
                "typescript",
                "java",
                "go",
                "rust",
                "c++",
                "c",
                "ruby",
                "php",
            ]


@dataclass
class CodeReviewerConfig(AgentConfig):
    """Configuration for code reviewer agent."""

    max_tokens: int = 2000
    temperature: float = 0.3  # Lower temperature for consistent review
    check_pep8: bool = True
    check_complexity: bool = True
    check_security: bool = True


# Default agent configurations
DEFAULT_GENERATOR_CONFIG = CodeGeneratorConfig()
DEFAULT_REVIEWER_CONFIG = CodeReviewerConfig()

# Agent configurations by name
AGENT_CONFIGS: Dict[str, AgentConfig] = {
    "code_generator": DEFAULT_GENERATOR_CONFIG,
    "code_reviewer": DEFAULT_REVIEWER_CONFIG,
}


# Model-agent compatibility matrix
# Maps model names to their compatibility with different agents
MODEL_AGENT_COMPATIBILITY: Dict[str, Dict[str, Any]] = {
    "qwen": {
        "code_generator": {
            "recommended": True,
            "config": {"max_tokens": 4000, "temperature": 0.7},
        },
        "code_reviewer": {
            "recommended": True,
            "config": {"max_tokens": 2000, "temperature": 0.3},
        },
    },
    "mistral": {
        "code_generator": {
            "recommended": True,
            "config": {"max_tokens": 4000, "temperature": 0.7},
        },
        "code_reviewer": {
            "recommended": True,
            "config": {"max_tokens": 2000, "temperature": 0.3},
        },
    },
    "tinyllama": {
        "code_generator": {
            "recommended": False,
            "config": {"max_tokens": 2000, "temperature": 0.7},
        },
        "code_reviewer": {
            "recommended": False,
            "config": {"max_tokens": 1000, "temperature": 0.3},
        },
    },
    "starcoder": {
        "code_generator": {
            "recommended": True,
            "config": {"max_tokens": 4000, "temperature": 0.7},
        },
        "code_reviewer": {
            "recommended": True,
            "config": {"max_tokens": 2000, "temperature": 0.3},
        },
    },
    "perplexity": {
        "code_generator": {
            "recommended": True,
            "config": {"max_tokens": 3000, "temperature": 0.7},
        },
        "code_reviewer": {
            "recommended": True,
            "config": {"max_tokens": 1500, "temperature": 0.3},
        },
    },
    "chadgpt": {
        "code_generator": {
            "recommended": True,
            "config": {"max_tokens": 3000, "temperature": 0.7},
        },
        "code_reviewer": {
            "recommended": True,
            "config": {"max_tokens": 1500, "temperature": 0.3},
        },
    },
}


def get_agent_config(agent_name: str) -> AgentConfig:
    """
    Get configuration for an agent.

    Args:
        agent_name: Name of the agent

    Returns:
        AgentConfig: Agent configuration

    Raises:
        KeyError: If agent not found
    """
    if agent_name not in AGENT_CONFIGS:
        raise KeyError(f"Unknown agent: {agent_name}")
    return AGENT_CONFIGS[agent_name]


def get_model_config_for_agent(model_name: str, agent_name: str) -> Dict[str, Any]:
    """
    Get model-specific configuration for an agent.

    Args:
        model_name: Name of the model
        agent_name: Name of the agent

    Returns:
        Dict[str, Any]: Model-agent specific configuration

    Raises:
        KeyError: If model or agent not found
    """
    if model_name not in MODEL_AGENT_COMPATIBILITY:
        raise KeyError(f"Unknown model: {model_name}")

    if agent_name not in MODEL_AGENT_COMPATIBILITY[model_name]:
        raise KeyError(f"Model {model_name} not compatible with agent {agent_name}")

    return MODEL_AGENT_COMPATIBILITY[model_name][agent_name]


def is_model_recommended_for_agent(model_name: str, agent_name: str) -> bool:
    """
    Check if a model is recommended for an agent.

    Args:
        model_name: Name of the model
        agent_name: Name of the agent

    Returns:
        bool: True if model is recommended

    Raises:
        KeyError: If model or agent not found
    """
    config = get_model_config_for_agent(model_name, agent_name)
    return config.get("recommended", False)


def get_compatible_models(agent_name: str) -> List[str]:
    """
    Get list of compatible models for an agent.

    Args:
        agent_name: Name of the agent

    Returns:
        List[str]: List of compatible model names
    """
    compatible = []
    for model_name in MODEL_AGENT_COMPATIBILITY:
        try:
            config = get_model_config_for_agent(model_name, agent_name)
            compatible.append(model_name)
        except KeyError:
            continue
    return compatible


def get_recommended_models(agent_name: str) -> List[str]:
    """
    Get list of recommended models for an agent.

    Args:
        agent_name: Name of the agent

    Returns:
        List[str]: List of recommended model names
    """
    recommended = []
    for model_name in MODEL_AGENT_COMPATIBILITY:
        try:
            if is_model_recommended_for_agent(model_name, agent_name):
                recommended.append(model_name)
        except KeyError:
            continue
    return recommended


# Default prompt templates
CODE_GENERATOR_PROMPT_TEMPLATE = """Generate {language} code for the following specification:

{task}

Requirements:
- Follow best practices for {language}
- Use clean, readable code style
- Add appropriate comments
- Handle edge cases
- Return only the code without markdown formatting

Code:"""


CODE_REVIEWER_PROMPT_TEMPLATE = """Review the following {language} code for quality, correctness, and best practices:

```{language}
{code}
```

Provide a comprehensive review covering:
1. Code quality and readability
2. Best practices and patterns
3. Potential bugs or issues
4. Security concerns
5. Performance optimizations
6. PEP8/PEP style compliance (if applicable)

Review:"""


def get_prompt_template(agent_name: str) -> str:
    """
    Get prompt template for an agent.

    Args:
        agent_name: Name of the agent

    Returns:
        str: Prompt template

    Raises:
        KeyError: If agent not found
    """
    templates = {
        "code_generator": CODE_GENERATOR_PROMPT_TEMPLATE,
        "code_reviewer": CODE_REVIEWER_PROMPT_TEMPLATE,
    }

    if agent_name not in templates:
        raise KeyError(f"Unknown agent: {agent_name}")

    return templates[agent_name]


__all__ = [
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
    "CODE_GENERATOR_PROMPT_TEMPLATE",
    "CODE_REVIEWER_PROMPT_TEMPLATE",
]
