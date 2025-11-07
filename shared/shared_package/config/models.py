"""
Unified model configuration for all projects.

Following Python Zen: "Explicit is better than implicit"
and "Simple is better than complex".
"""

import os
from enum import Enum
from typing import Dict, Any


class ModelType(Enum):
    """Model types."""
    LOCAL = "local"
    EXTERNAL = "external"


class ModelName(Enum):
    """Supported model names."""
    QWEN = "qwen"
    MISTRAL = "mistral"
    TINYLLAMA = "tinyllama"
    STARCODER = "starcoder"
    PERPLEXITY = "perplexity"
    CHADGPT = "chadgpt"


class ModelPort(Enum):
    """Local model ports."""
    QWEN = 8000
    MISTRAL = 8001
    TINYLLAMA = 8002
    STARCODER = 8003


# Unified model configuration
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    ModelName.QWEN.value: {
        "type": ModelType.LOCAL.value,
        "port": ModelPort.QWEN.value,
        "url": f"http://localhost:{ModelPort.QWEN.value}",
        "display_name": "Qwen-4B",
        "description": "Быстрые ответы, хорошее качество",
        "openai_compatible": True
    },
    ModelName.MISTRAL.value: {
        "type": ModelType.LOCAL.value,
        "port": ModelPort.MISTRAL.value,
        "url": f"http://localhost:{ModelPort.MISTRAL.value}",
        "display_name": "Mistral-7B",
        "description": "Высокое качество, рекомендована",
        "openai_compatible": True
    },
    ModelName.TINYLLAMA.value: {
        "type": ModelType.LOCAL.value,
        "port": ModelPort.TINYLLAMA.value,
        "url": f"http://localhost:{ModelPort.TINYLLAMA.value}",
        "display_name": "TinyLlama-1.1B",
        "description": "Компактная, быстрая",
        "openai_compatible": True
    },
    ModelName.STARCODER.value: {
        "type": ModelType.LOCAL.value,
        "port": ModelPort.STARCODER.value,
        "url": f"http://localhost:{ModelPort.STARCODER.value}",
        "display_name": "TechxGenus/StarCoder2-7B-Instruct",
        "description": "Code generation specialist with instruction tuning",
        "openai_compatible": True
    },
    ModelName.PERPLEXITY.value: {
        "type": ModelType.EXTERNAL.value,
        "url": "https://api.perplexity.ai/chat/completions",
        "display_name": "Perplexity Sonar",
        "description": "Внешний API"
    },
    ModelName.CHADGPT.value: {
        "type": ModelType.EXTERNAL.value,
        "url": "https://ask.chadgpt.ru/api/public/gpt-5-mini",
        "display_name": "ChadGPT",
        "description": "Внешний API"
    }
}

# Backward compatibility mappings
MODEL_PORTS = {
    ModelName.QWEN.value: ModelPort.QWEN.value,
    ModelName.MISTRAL.value: ModelPort.MISTRAL.value,
    ModelName.TINYLLAMA.value: ModelPort.TINYLLAMA.value,
    ModelName.STARCODER.value: ModelPort.STARCODER.value
}

LOCAL_MODELS = {
    ModelName.QWEN.value: MODEL_CONFIGS[ModelName.QWEN.value]["url"],
    ModelName.MISTRAL.value: MODEL_CONFIGS[ModelName.MISTRAL.value]["url"],
    ModelName.TINYLLAMA.value: MODEL_CONFIGS[ModelName.TINYLLAMA.value]["url"],
    ModelName.STARCODER.value: MODEL_CONFIGS[ModelName.STARCODER.value]["url"]
}


def get_model_config(model_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dict[str, Any]: Model configuration
        
    Raises:
        KeyError: If model not found
    """
    if model_name not in MODEL_CONFIGS:
        raise KeyError(f"Unknown model: {model_name}")
    
    config = MODEL_CONFIGS[model_name].copy()
    
    # Override URL if environment variable is set (for Docker containers)
    # Priority: 1) Model-specific URL (e.g., MISTRAL_URL), 2) Generic LLM_URL
    env_var_name = f"{model_name.upper()}_URL"
    env_url = os.getenv(env_var_name)
    if not env_url:
        # Fallback to generic LLM_URL if model-specific URL is not set
        env_url = os.getenv("LLM_URL")
    
    if env_url:
        config["url"] = env_url
    
    return config


def get_local_models() -> Dict[str, str]:
    """
    Get all local model configurations.
    
    Returns:
        Dict[str, str]: Local model name to URL mapping
    """
    return LOCAL_MODELS.copy()


def get_model_port(model_name: str) -> int:
    """
    Get port for a local model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        int: Model port
        
    Raises:
        KeyError: If model not found or not local
    """
    config = get_model_config(model_name)
    if config["type"] != ModelType.LOCAL.value:
        raise KeyError(f"Model {model_name} is not local")
    return config["port"]


def is_local_model(model_name: str) -> bool:
    """
    Check if model is local.
    
    Args:
        model_name: Name of the model
        
    Returns:
        bool: True if model is local
    """
    try:
        config = get_model_config(model_name)
        return config["type"] == ModelType.LOCAL.value
    except KeyError:
        return False
