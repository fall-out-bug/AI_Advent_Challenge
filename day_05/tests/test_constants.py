"""
Tests for constants module.
"""

import pytest

from utils.constants import (
    DEFAULT_HTTP_TIMEOUT,
    QUICK_HTTP_TIMEOUT,
    MAX_HTTP_RETRIES,
    HTTP_RETRY_DELAY,
    HTTP_BACKOFF_FACTOR,
    CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
    MIN_TEMPERATURE,
    MAX_TEMPERATURE,
    DEFAULT_TEMPERATURE,
    INTERACTIVE_TEMPERATURE_LOW,
    INTERACTIVE_TEMPERATURE_MEDIUM,
    INTERACTIVE_TEMPERATURE_HIGH,
    DEFAULT_MAX_TOKENS,
    QUICK_MAX_TOKENS,
    LONG_MAX_TOKENS,
    TERMINAL_WIDTH_DEFAULT,
    TERMINAL_HEIGHT_DEFAULT,
    PROMPT_PREVIEW_LENGTH,
    USER_MESSAGE_PREVIEW_LENGTH,
    PERPLEXITY_MODEL,
    PERPLEXITY_URL,
    CHADGPT_URL,
    ERROR_CONNECTION_FAILED,
    ERROR_REQUEST_TIMEOUT,
    ERROR_HTTP_STATUS,
    ERROR_UNEXPECTED,
    SUCCESS_TEMPERATURE_SET,
    SUCCESS_API_SWITCHED,
    SUCCESS_EXPLAIN_MODE_ON,
    SUCCESS_EXPLAIN_MODE_OFF,
    SUCCESS_ADVICE_MODE_ON,
    SUCCESS_HISTORY_ON,
    SUCCESS_HISTORY_OFF,
    SUCCESS_HISTORY_CLEARED,
    ERROR_INVALID_TEMP_FORMAT,
    ERROR_UNKNOWN_API,
    ERROR_HISTORY_LOCAL_ONLY,
    ERROR_NO_API_CONFIGURED,
    ERROR_API_SETUP_INSTRUCTIONS,
    DEFAULT_SYSTEM_PROMPT,
    TRIGGER_LOW_TEMPERATURE,
    TRIGGER_MEDIUM_TEMPERATURE,
    TRIGGER_HIGH_TEMPERATURE,
    COMMAND_EXIT,
    COMMAND_EXPLAIN_ON,
    COMMAND_EXPLAIN_OFF,
    COMMAND_ADVICE_ON,
    COMMAND_TEMP_PREFIX,
    COMMAND_API_PREFIX,
    COMMAND_HISTORY_ON,
    COMMAND_HISTORY_OFF,
    COMMAND_CLEAR_HISTORY,
    UNICODE_SEPARATORS
)


class TestHTTPConstants:
    """Test HTTP-related constants."""
    
    def test_http_timeouts(self):
        """Test HTTP timeout constants."""
        assert DEFAULT_HTTP_TIMEOUT == 30.0
        assert QUICK_HTTP_TIMEOUT == 5.0
        assert isinstance(DEFAULT_HTTP_TIMEOUT, float)
        assert isinstance(QUICK_HTTP_TIMEOUT, float)
    
    def test_http_retry_constants(self):
        """Test HTTP retry constants."""
        assert MAX_HTTP_RETRIES == 3
        assert HTTP_RETRY_DELAY == 1.0
        assert HTTP_BACKOFF_FACTOR == 2.0
        assert isinstance(MAX_HTTP_RETRIES, int)
        assert isinstance(HTTP_RETRY_DELAY, float)
        assert isinstance(HTTP_BACKOFF_FACTOR, float)
    
    def test_circuit_breaker_constants(self):
        """Test circuit breaker constants."""
        assert CIRCUIT_BREAKER_FAILURE_THRESHOLD == 5
        assert CIRCUIT_BREAKER_RECOVERY_TIMEOUT == 60.0
        assert isinstance(CIRCUIT_BREAKER_FAILURE_THRESHOLD, int)
        assert isinstance(CIRCUIT_BREAKER_RECOVERY_TIMEOUT, float)


class TestTemperatureConstants:
    """Test temperature-related constants."""
    
    def test_temperature_limits(self):
        """Test temperature limit constants."""
        assert MIN_TEMPERATURE == 0.0
        assert MAX_TEMPERATURE == 2.0
        assert DEFAULT_TEMPERATURE == 0.5
        assert isinstance(MIN_TEMPERATURE, float)
        assert isinstance(MAX_TEMPERATURE, float)
        assert isinstance(DEFAULT_TEMPERATURE, float)
    
    def test_interactive_temperatures(self):
        """Test interactive temperature constants."""
        assert INTERACTIVE_TEMPERATURE_LOW == 0.0
        assert INTERACTIVE_TEMPERATURE_MEDIUM == 0.7
        assert INTERACTIVE_TEMPERATURE_HIGH == 1.2
        assert isinstance(INTERACTIVE_TEMPERATURE_LOW, float)
        assert isinstance(INTERACTIVE_TEMPERATURE_MEDIUM, float)
        assert isinstance(INTERACTIVE_TEMPERATURE_HIGH, float)


class TestTokenConstants:
    """Test token-related constants."""
    
    def test_token_limits(self):
        """Test token limit constants."""
        assert DEFAULT_MAX_TOKENS == 800
        assert QUICK_MAX_TOKENS == 1
        assert LONG_MAX_TOKENS == 1000
        assert isinstance(DEFAULT_MAX_TOKENS, int)
        assert isinstance(QUICK_MAX_TOKENS, int)
        assert isinstance(LONG_MAX_TOKENS, int)


class TestUIConstants:
    """Test UI-related constants."""
    
    def test_terminal_dimensions(self):
        """Test terminal dimension constants."""
        assert TERMINAL_WIDTH_DEFAULT == 100
        assert TERMINAL_HEIGHT_DEFAULT == 20
        assert isinstance(TERMINAL_WIDTH_DEFAULT, int)
        assert isinstance(TERMINAL_HEIGHT_DEFAULT, int)
    
    def test_preview_lengths(self):
        """Test preview length constants."""
        assert PROMPT_PREVIEW_LENGTH == 120
        assert USER_MESSAGE_PREVIEW_LENGTH == 80
        assert isinstance(PROMPT_PREVIEW_LENGTH, int)
        assert isinstance(USER_MESSAGE_PREVIEW_LENGTH, int)


class TestAPIConstants:
    """Test API-related constants."""
    
    def test_api_urls(self):
        """Test API URL constants."""
        assert PERPLEXITY_URL == "https://api.perplexity.ai/chat/completions"
        assert CHADGPT_URL == "https://ask.chadgpt.ru/api/public/gpt-5-mini"
        assert isinstance(PERPLEXITY_URL, str)
        assert isinstance(CHADGPT_URL, str)
    
    def test_api_model(self):
        """Test API model constant."""
        assert PERPLEXITY_MODEL == "sonar-pro"
        assert isinstance(PERPLEXITY_MODEL, str)


class TestMessageConstants:
    """Test message constants."""
    
    def test_error_messages(self):
        """Test error message constants."""
        assert ERROR_CONNECTION_FAILED == "Failed to connect to {url}: {error}"
        assert ERROR_REQUEST_TIMEOUT == "Request to {url} timed out: {error}"
        assert ERROR_HTTP_STATUS == "HTTP error for {url}: {error}"
        assert ERROR_UNEXPECTED == "Unexpected error with {url}: {error}"
        assert all(isinstance(msg, str) for msg in [
            ERROR_CONNECTION_FAILED, ERROR_REQUEST_TIMEOUT, 
            ERROR_HTTP_STATUS, ERROR_UNEXPECTED
        ])
    
    def test_success_messages(self):
        """Test success message constants."""
        assert SUCCESS_TEMPERATURE_SET == "Температура установлена: {temp:.2f}"
        assert SUCCESS_API_SWITCHED == "Переключено на: {api}"
        assert SUCCESS_EXPLAIN_MODE_ON == "Режим пояснений включен"
        assert SUCCESS_EXPLAIN_MODE_OFF == "Режим пояснений и советчика выключен"
        assert SUCCESS_ADVICE_MODE_ON == "Режим советчика включен"
        assert SUCCESS_HISTORY_ON == "История сообщений включена"
        assert SUCCESS_HISTORY_OFF == "История сообщений выключена"
        assert SUCCESS_HISTORY_CLEARED == "История сообщений очищена"
        assert all(isinstance(msg, str) for msg in [
            SUCCESS_TEMPERATURE_SET, SUCCESS_API_SWITCHED,
            SUCCESS_EXPLAIN_MODE_ON, SUCCESS_EXPLAIN_MODE_OFF,
            SUCCESS_ADVICE_MODE_ON, SUCCESS_HISTORY_ON,
            SUCCESS_HISTORY_OFF, SUCCESS_HISTORY_CLEARED
        ])
    
    def test_russian_error_messages(self):
        """Test Russian error message constants."""
        assert ERROR_INVALID_TEMP_FORMAT == "Неверный формат: temp <value>"
        assert ERROR_UNKNOWN_API == "Неизвестный API: {api}"
        assert ERROR_HISTORY_LOCAL_ONLY == "История доступна только для локальных моделей"
        assert ERROR_NO_API_CONFIGURED == "Ни один API ключ не настроен и локальные модели недоступны!"
        assert ERROR_API_SETUP_INSTRUCTIONS == "Установите CHAD_API_KEY или PERPLEXITY_API_KEY, или запустите локальные модели"
        assert all(isinstance(msg, str) for msg in [
            ERROR_INVALID_TEMP_FORMAT, ERROR_UNKNOWN_API,
            ERROR_HISTORY_LOCAL_ONLY, ERROR_NO_API_CONFIGURED,
            ERROR_API_SETUP_INSTRUCTIONS
        ])


class TestSystemConstants:
    """Test system-related constants."""
    
    def test_system_prompt(self):
        """Test system prompt constant."""
        assert DEFAULT_SYSTEM_PROMPT == "Ты пожилой человек, который ехидно подшучивает. Отвечай на русском, лаконично, без ссылок."
        assert isinstance(DEFAULT_SYSTEM_PROMPT, str)
        assert len(DEFAULT_SYSTEM_PROMPT) > 0
    
    def test_trigger_words(self):
        """Test trigger word constants."""
        assert TRIGGER_LOW_TEMPERATURE == ["не душни", "не души", "не дави"]
        assert TRIGGER_MEDIUM_TEMPERATURE == ["потише", "тише", "спокойнее"]
        assert TRIGGER_HIGH_TEMPERATURE == ["разгоняй", "разгоня", "быстрее"]
        assert all(isinstance(triggers, list) for triggers in [
            TRIGGER_LOW_TEMPERATURE, TRIGGER_MEDIUM_TEMPERATURE, TRIGGER_HIGH_TEMPERATURE
        ])
        assert all(isinstance(word, str) for triggers in [
            TRIGGER_LOW_TEMPERATURE, TRIGGER_MEDIUM_TEMPERATURE, TRIGGER_HIGH_TEMPERATURE
        ] for word in triggers)
    
    def test_commands(self):
        """Test command constants."""
        assert COMMAND_EXIT == "покеда"
        assert COMMAND_EXPLAIN_ON == "объясняй"
        assert COMMAND_EXPLAIN_OFF == "надоел"
        assert COMMAND_ADVICE_ON == "дай совет"
        assert COMMAND_TEMP_PREFIX == "temp "
        assert COMMAND_API_PREFIX == "api "
        assert COMMAND_HISTORY_ON == "история вкл"
        assert COMMAND_HISTORY_OFF == "история выкл"
        assert COMMAND_CLEAR_HISTORY == "очисти историю"
        assert all(isinstance(cmd, str) for cmd in [
            COMMAND_EXIT, COMMAND_EXPLAIN_ON, COMMAND_EXPLAIN_OFF,
            COMMAND_ADVICE_ON, COMMAND_TEMP_PREFIX, COMMAND_API_PREFIX,
            COMMAND_HISTORY_ON, COMMAND_HISTORY_OFF, COMMAND_CLEAR_HISTORY
        ])
    
    def test_unicode_separators(self):
        """Test unicode separator constants."""
        assert isinstance(UNICODE_SEPARATORS, list)
        assert len(UNICODE_SEPARATORS) > 0
        assert all(isinstance(sep, str) for sep in UNICODE_SEPARATORS)
        assert "-" in UNICODE_SEPARATORS
        assert "_" in UNICODE_SEPARATORS
        assert "," in UNICODE_SEPARATORS
        assert "." in UNICODE_SEPARATORS
