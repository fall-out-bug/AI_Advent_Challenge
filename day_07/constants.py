"""Constants for the multi-agent system."""

# Startup and retry configuration
MAX_STARTUP_RETRIES = 30
RETRY_DELAY_SECONDS = 2
DEFAULT_TIMEOUT = 600.0  # 10 minutes for local models (StarCoder2-7B needs more time)

# HTTP client configuration
HTTP_TIMEOUT = 600.0  # 10 minutes for local models
HTTP_MAX_RETRIES = 3

# Model configuration
DEFAULT_MODEL = "starcoder"
SUPPORTED_MODELS = ["starcoder", "mistral", "qwen", "tinyllama"]

# Model-specific settings
MODEL_SPECIFIC_SETTINGS = {
    "starcoder": {
        "generator_temperature": 0.3,
        "reviewer_temperature": 0.2,
        "generator_max_tokens": 1500,
        "reviewer_max_tokens": 1200,
    },
    "mistral": {
        "generator_temperature": 0.4,
        "reviewer_temperature": 0.3,
        "generator_max_tokens": 1500,
        "reviewer_max_tokens": 1200,
    },
    "qwen": {
        "generator_temperature": 0.3,
        "reviewer_temperature": 0.2,
        "generator_max_tokens": 1200,
        "reviewer_max_tokens": 1000,
    },
    "tinyllama": {
        "generator_temperature": 0.2,
        "reviewer_temperature": 0.1,
        "generator_max_tokens": 1000,
        "reviewer_max_tokens": 800,
    },
}

# StarCoder configuration (TechxGenus/starcoder2-7b-instruct)
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.7
GENERATOR_MAX_TOKENS = 1500
GENERATOR_TEMPERATURE = 0.3
REVIEWER_MAX_TOKENS = 1200
REVIEWER_TEMPERATURE = 0.2

# API configuration
DEFAULT_PORT_GENERATOR = 9001
DEFAULT_PORT_REVIEWER = 9002
DEFAULT_STARCODER_PORT = 8003

# Rate limiting
RATE_LIMIT_PER_MINUTE = 10
RATE_LIMIT_PER_HOUR = 100

# Input validation limits
MAX_CODE_LENGTH = 10000
MAX_FEEDBACK_LENGTH = 5000
MAX_TASK_DESCRIPTION_LENGTH = 2000
MAX_REQUIREMENTS_COUNT = 10

# Health check configuration
HEALTH_CHECK_INTERVAL = 30
HEALTH_CHECK_TIMEOUT = 10
HEALTH_CHECK_START_PERIOD = 60
HEALTH_CHECK_RETRIES = 3

# File and directory configuration
RESULTS_DIR = "results"
MAX_RESULTS_FILES = 100

# Error messages
GENERIC_ERROR_MESSAGE = "An internal error occurred. Please try again."
VALIDATION_ERROR_MESSAGE = "Invalid input provided."
RATE_LIMIT_ERROR_MESSAGE = "Rate limit exceeded. Please try again later."

# Environment variables
HF_TOKEN_ENV_VAR = "HF_TOKEN"
MODEL_NAME_ENV_VAR = "MODEL_NAME"
STARCODER_URL_ENV_VAR = "STARCODER_URL"
PORT_ENV_VAR = "PORT"
AGENT_TYPE_ENV_VAR = "AGENT_TYPE"
GENERATOR_URL_ENV_VAR = "GENERATOR_URL"
REVIEWER_URL_ENV_VAR = "REVIEWER_URL"

# Logging configuration
LOG_LEVEL_ENV_VAR = "LOG_LEVEL"
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Regex patterns for code extraction
CODE_BLOCK_PATTERN = r"```(?:python)?\s*(.*?)```"
FUNCTION_DEF_PATTERN = r"(def\s+\w+.*?)(?=\n\ndef|\n\nclass|\Z)"
TEST_PATTERNS = [
    r"### TESTS\s*```(?:python)?\s*(.*?)```",
    r"TESTS:\s*```(?:python)?\s*(.*?)```",
    r"```python\s*(import pytest.*?)```",
]
PYTEST_PATTERN = r"(import pytest.*?)(?=\n\n###|\Z)"

# JSON extraction patterns
JSON_BLOCK_PATTERN = r"```json\s*(.*?)```"

# Metadata extraction patterns
COMPLEXITY_PATTERN = r"Complexity:\s*(\w+)"
LOC_PATTERN = r"Lines of Code:\s*(\d+)"
DEPS_PATTERN = r"Dependencies:\s*\[(.*?)\]"
TIME_PATTERN = r"Estimated Time:\s*([^\n]+)"

# PEP8 analysis patterns
PEP8_COMPLIANCE_PATTERN = r"PEP8 COMPLIANCE[:\s]*(\w+)"
PEP8_SCORE_PATTERN = r"SCORE[:\s]*(\d+(?:\.\d+)?)"
PEP8_VIOLATIONS_PATTERN = r"VIOLATIONS[:\s]*\n((?:[-*]\s*.*\n?)*)"
PEP8_RECOMMENDATIONS_PATTERN = r"RECOMMENDATIONS[:\s]*\n((?:[-*]\s*.*\n?)*)"

# Test coverage patterns
COVERAGE_ASSESSMENT_PATTERN = r"COVERAGE ASSESSMENT[:\s]*(\w+)"
COVERED_SCENARIOS_PATTERN = r"COVERED SCENARIOS[:\s]*\n((?:[-*]\s*.*\n?)*)"
MISSING_SCENARIOS_PATTERN = r"MISSING SCENARIOS[:\s]*\n((?:[-*]\s*.*\n?)*)"
COVERAGE_RECOMMENDATIONS_PATTERN = r"RECOMMENDATIONS[:\s]*\n((?:[-*]\s*.*\n?)*)"

# List item extraction pattern
LIST_ITEM_PATTERN = r"[-*]\s*(.+?)(?=\n[-*]|\n\n|\Z)"
