"""
Constants for the local model testing system.

This module re-exports constants from shared SDK for backward compatibility.
Following Python Zen: "Explicit is better than implicit".
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Re-export from shared SDK
from shared.config.constants import (
    DEFAULT_TIMEOUT,
    QUICK_TIMEOUT,
    TEST_TIMEOUT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    TEST_MAX_TOKENS,
    DIFFICULTY_LEVELS,
    LOGICAL_KEYWORDS,
    STEP_PATTERNS,
    REPORT_FILENAME_PREFIX,
    REPORT_TIMESTAMP_FORMAT,
    DISPLAY_TIMESTAMP_FORMAT
)

from shared.config.models import (
    ModelName,
    ModelPort,
    MODEL_PORTS
)
