"""
API key management for external models.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import os
from pathlib import Path
from typing import Optional, Dict


def load_api_key_from_file(file_path: Path, key_name: str) -> Optional[str]:
    """
    Load API key from file, looking for line with prefix key_name:.

    Args:
        file_path: Path to the API key file
        key_name: Name of the API (perplexity, chadgpt)

    Returns:
        Optional[str]: API key if found, None otherwise
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key_name}:") and len(line) > len(key_name) + 1:
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def get_api_key(api_type: str = "perplexity") -> Optional[str]:
    """
    Get API key for specified API type.

    Args:
        api_type: Type of API (perplexity, chadgpt)

    Returns:
        Optional[str]: API key if configured, None otherwise
    """
    # Try to load from file first
    config_file = Path(__file__).parent.parent / "api_key.txt"
    api_key = load_api_key_from_file(config_file, api_type)

    if api_key:
        return api_key

    # Fallback to environment variables
    env_var_map = {
        "perplexity": "PERPLEXITY_API_KEY",
        "chadgpt": "CHAD_API_KEY"
    }

    env_var = env_var_map.get(api_type)
    if env_var:
        return os.getenv(env_var)

    return None


def is_api_key_configured(api_type: str = "perplexity") -> bool:
    """
    Check if API key is configured for specified API type.

    Args:
        api_type: Type of API (perplexity, chadgpt)

    Returns:
        bool: True if API key is configured
    """
    key = get_api_key(api_type)
    return key is not None and key.strip() != ""


def get_available_external_apis() -> Dict[str, bool]:
    """
    Get availability status of external APIs.

    Returns:
        Dict[str, bool]: API name to availability mapping
    """
    return {
        "perplexity": is_api_key_configured("perplexity"),
        "chadgpt": is_api_key_configured("chadgpt")
    }
