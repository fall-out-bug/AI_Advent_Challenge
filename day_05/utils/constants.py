"""
Constants and magic numbers for terminal chat.

Following Python Zen: "Explicit is better than implicit"
and "There should be one obvious way to do it".
"""

# HTTP Configuration
DEFAULT_HTTP_TIMEOUT = 30.0
QUICK_HTTP_TIMEOUT = 5.0
MAX_HTTP_RETRIES = 3
HTTP_RETRY_DELAY = 1.0
HTTP_BACKOFF_FACTOR = 2.0

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60.0

# Temperature Configuration
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0
DEFAULT_TEMPERATURE = 0.5
INTERACTIVE_TEMPERATURE_LOW = 0.0
INTERACTIVE_TEMPERATURE_MEDIUM = 0.7
INTERACTIVE_TEMPERATURE_HIGH = 1.2

# Token Configuration
DEFAULT_MAX_TOKENS = 800
QUICK_MAX_TOKENS = 1
LONG_MAX_TOKENS = 1000

# UI Configuration
TERMINAL_WIDTH_DEFAULT = 100
TERMINAL_HEIGHT_DEFAULT = 20
PROMPT_PREVIEW_LENGTH = 120
USER_MESSAGE_PREVIEW_LENGTH = 80

# API Configuration
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
CHADGPT_URL = "https://ask.chadgpt.ru/api/public/gpt-5-mini"

# Error Messages
ERROR_CONNECTION_FAILED = "Failed to connect to {url}: {error}"
ERROR_REQUEST_TIMEOUT = "Request to {url} timed out: {error}"
ERROR_HTTP_STATUS = "HTTP error for {url}: {error}"
ERROR_UNEXPECTED = "Unexpected error with {url}: {error}"

# Success Messages
SUCCESS_TEMPERATURE_SET = "Температура установлена: {temp:.2f}"
SUCCESS_API_SWITCHED = "Переключено на: {api}"
SUCCESS_EXPLAIN_MODE_ON = "Режим пояснений включен"
SUCCESS_EXPLAIN_MODE_OFF = "Режим пояснений и советчика выключен"
SUCCESS_ADVICE_MODE_ON = "Режим советчика включен"
SUCCESS_HISTORY_ON = "История сообщений включена"
SUCCESS_HISTORY_OFF = "История сообщений выключена"
SUCCESS_HISTORY_CLEARED = "История сообщений очищена"

# Error Messages (Russian)
ERROR_INVALID_TEMP_FORMAT = "Неверный формат: temp <value>"
ERROR_UNKNOWN_API = "Неизвестный API: {api}"
ERROR_HISTORY_LOCAL_ONLY = "История доступна только для локальных моделей"
ERROR_NO_API_CONFIGURED = "Ни один API ключ не настроен и локальные модели недоступны!"
ERROR_API_SETUP_INSTRUCTIONS = "Установите CHAD_API_KEY или PERPLEXITY_API_KEY, или запустите локальные модели"

# System Prompts
DEFAULT_SYSTEM_PROMPT = "Ты пожилой человек, который ехидно подшучивает. Отвечай на русском, лаконично, без ссылок."

# Interactive Triggers
TRIGGER_LOW_TEMPERATURE = ["не душни", "не души", "не дави"]
TRIGGER_MEDIUM_TEMPERATURE = ["потише", "тише", "спокойнее"]
TRIGGER_HIGH_TEMPERATURE = ["разгоняй", "разгоня", "быстрее"]

# Commands
COMMAND_EXIT = "покеда"
COMMAND_EXPLAIN_ON = "объясняй"
COMMAND_EXPLAIN_OFF = "надоел"
COMMAND_ADVICE_ON = "дай совет"
COMMAND_TEMP_PREFIX = "temp "
COMMAND_API_PREFIX = "api "
COMMAND_HISTORY_ON = "история вкл"
COMMAND_HISTORY_OFF = "история выкл"
COMMAND_CLEAR_HISTORY = "очисти историю"

# Unicode Separators for Text Normalization
UNICODE_SEPARATORS = [
    "\u2013", "\u2014", "-", "_", "|", ",", ".", "!", "?", 
    "\u00A0", "\u2019", "\u2018", "\u201c", "\u201d", 
    "\"", "'", ":", ";", "(", ")", "[", "]", "{", "}"
]
