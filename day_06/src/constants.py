"""
Constants for the local model testing system.

This module contains all configuration constants to avoid magic numbers
and improve code maintainability.
Following Python Zen: "Explicit is better than implicit".
"""

from enum import Enum, auto


class ModelName(Enum):
    """Enum for model names following Python Zen principles."""
    QWEN = "qwen"
    MISTRAL = "mistral"
    TINYLLAMA = "tinyllama"


class ModelPort(Enum):
    """Enum for model ports following Python Zen principles."""
    QWEN = 8000
    MISTRAL = 8001
    TINYLLAMA = 8002


# Model configuration - maintaining backward compatibility
MODEL_PORTS = {
    ModelName.QWEN.value: ModelPort.QWEN.value,
    ModelName.MISTRAL.value: ModelPort.MISTRAL.value,
    ModelName.TINYLLAMA.value: ModelPort.TINYLLAMA.value
}

# HTTP client configuration
DEFAULT_TIMEOUT = 120.0
QUICK_TIMEOUT = 5.0

# Model generation parameters
MAX_TOKENS = 10000
DEFAULT_TEMPERATURE = 0.7
TEST_MAX_TOKENS = 1

# Analysis configuration
DIFFICULTY_LEVELS = {
    "MIN": 1,
    "MAX": 5
}

# Logical keywords for analysis
LOGICAL_KEYWORDS = [
    "если", "значит", "поэтому", "следовательно", "отсюда", 
    "из этого", "получается", "вывод", "рассуждение", "логика",
    "шаг", "этап", "сначала", "затем", "далее", "в итоге"
]

# Step-by-step structure patterns
STEP_PATTERNS = [
    r'\d+[\.\)]\s',  # 1. or 1)
    r'шаг\s*\d+',    # step 1
    r'этап\s*\d+',   # stage 1
    r'сначала',      # first
    r'затем',        # then
    r'далее',        # further
    r'в итоге'       # in conclusion
]

# Report configuration
REPORT_FILENAME_PREFIX = "model_test_report_"
REPORT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
DISPLAY_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
