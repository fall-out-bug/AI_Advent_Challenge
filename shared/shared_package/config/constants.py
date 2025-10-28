"""Common constants for all projects."""

# HTTP client configuration
DEFAULT_TIMEOUT = 600.0
QUICK_TIMEOUT = 5.0
TEST_TIMEOUT = 30.0

# Model generation parameters
DEFAULT_MAX_TOKENS = 10000
DEFAULT_TEMPERATURE = 0.7
TEST_MAX_TOKENS = 1

# Analysis configuration
DIFFICULTY_LEVELS = {
    "MIN": 1,
    "MAX": 5
}

# Logical keywords for analysis
LOGICAL_KEYWORDS = ["если", "значит", "поэтому", "следовательно", "отсюда", "из этого", "получается", "вывод", "рассуждение", "логика", "шаг", "этап", "сначала", "затем", "далее", "в итоге"]
STEP_PATTERNS = [r'\d+[\.\)]\s', r'шаг\s*\d+', r'этап\s*\d+', r'сначала', r'затем', r'далее', r'в итоге']

# Report configuration
REPORT_FILENAME_PREFIX = "model_test_report_"
REPORT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
DISPLAY_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# API configuration
DEFAULT_API_MODEL = "sonar-pro"
DEFAULT_CHADGPT_MODEL = "gpt-5-mini"

# Temperature configuration
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0
DEFAULT_TEMPERATURE_CLAMP = 1.5

# Token limits
MIN_TOKENS = 1
MAX_TOKENS_LIMIT = 100000

# Advice mode configuration
MAX_ADVICE_QUESTIONS = 5
ADVICE_TRIGGER_PHRASES = ["дай совет", "дай мне совет", "нужен совет", "посоветуй", "что посоветуешь", "как быть", "что делать"]

# UI configuration
TERMINAL_WIDTH = 60
PROMPT_PREFIX = "🤔 Вы"
RESPONSE_PREFIX = "👴 Дедушка"
