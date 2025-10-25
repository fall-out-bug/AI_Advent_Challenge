"""
Tests for utilities module.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from datetime import datetime

from utils.logging import StructuredLogger, RequestLogger, LoggerFactory
from utils.statistics import StatisticsCalculator, StatisticsReporter, StatisticsSummary
from utils.formatters import TextFormatter, ConsoleFormatter, FormatConfig
from utils.retry import (
    RetryHandler, CircuitBreaker, ResilientClient, RetryConfig, 
    CircuitBreakerConfig, RetryStrategy, CircuitBreakerState,
    CircuitBreakerOpenError
)
from models.data_models import ExperimentResult, CompressionResult, TokenInfo


class TestStructuredLogger:
    """Test StructuredLogger functionality."""
    
    def test_logger_creation(self):
        """Test logger creation."""
        logger = StructuredLogger("test", "INFO", "text")
        assert logger.name == "test"
        assert logger.level == "INFO"
        assert logger.format_type == "text"
    
    def test_logging_levels(self):
        """Test different logging levels."""
        logger = StructuredLogger("test", "DEBUG", "text")
        
        # Test that methods exist and can be called
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")
    
    def test_logging_with_kwargs(self):
        """Test logging with additional kwargs."""
        logger = StructuredLogger("test", "INFO", "text")
        logger.info("test message", user_id="123", action="test")


class TestRequestLogger:
    """Test RequestLogger functionality."""
    
    def test_request_logger_creation(self):
        """Test request logger creation."""
        logger = StructuredLogger("test")
        request_logger = RequestLogger(logger)
        assert request_logger.logger == logger
        assert request_logger.request_id is None
    
    def test_request_id_setting(self):
        """Test setting request ID."""
        logger = StructuredLogger("test")
        request_logger = RequestLogger(logger)
        request_logger.set_request_id("req-123")
        assert request_logger.request_id == "req-123"
    
    def test_request_logging_methods(self):
        """Test request logging methods."""
        logger = StructuredLogger("test")
        request_logger = RequestLogger(logger)
        request_logger.set_request_id("req-123")
        
        request_logger.log_request_start("GET", "/api/test")
        request_logger.log_request_end(200, 1.5)
        request_logger.log_request_error("Connection timeout")


class TestLoggerFactory:
    """Test LoggerFactory functionality."""
    
    def test_create_logger(self):
        """Test creating logger."""
        logger = LoggerFactory.create_logger("test", "DEBUG", "json")
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test"
    
    def test_create_request_logger(self):
        """Test creating request logger."""
        request_logger = LoggerFactory.create_request_logger("test")
        assert isinstance(request_logger, RequestLogger)
    
    def test_setup_root_logger(self):
        """Test setting up root logger."""
        LoggerFactory.setup_root_logger("INFO", "text")


class TestStatisticsCalculator:
    """Test StatisticsCalculator functionality."""
    
    def test_calculate_average(self):
        """Test average calculation."""
        calculator = StatisticsCalculator()
        
        assert calculator.calculate_average([1, 2, 3, 4, 5]) == 3.0
        assert calculator.calculate_average([]) == 0.0
        assert calculator.calculate_average([10]) == 10.0
    
    def test_calculate_median(self):
        """Test median calculation."""
        calculator = StatisticsCalculator()
        
        assert calculator.calculate_median([1, 2, 3, 4, 5]) == 3
        assert calculator.calculate_median([1, 2, 3, 4]) == 2.5
        assert calculator.calculate_median([]) == 0.0
    
    def test_calculate_percentile(self):
        """Test percentile calculation."""
        calculator = StatisticsCalculator()
        
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        # numpy.percentile uses interpolation, so 50th percentile might be 5.5
        result = calculator.calculate_percentile(values, 50)
        assert 5.0 <= result <= 6.0  # Allow for interpolation
        # 90th percentile of [1,2,3,4,5,6,7,8,9,10] should be around 9-10
        result_90 = calculator.calculate_percentile(values, 90)
        assert 9.0 <= result_90 <= 10.0
        assert calculator.calculate_percentile([], 50) == 0.0
    
    def test_calculate_compression_stats(self):
        """Test compression statistics calculation."""
        calculator = StatisticsCalculator()
        
        results = [
            CompressionResult(
                original_text="test1", compressed_text="t1", 
                original_tokens=100, compressed_tokens=50,
                compression_ratio=0.5, strategy_used="truncation"
            ),
            CompressionResult(
                original_text="test2", compressed_text="t2",
                original_tokens=200, compressed_tokens=100,
                compression_ratio=0.5, strategy_used="keywords"
            ),
        ]
        
        stats = calculator.calculate_compression_stats(results)
        assert stats["avg_ratio"] == 0.5
        assert stats["min_ratio"] == 0.5
        assert stats["max_ratio"] == 0.5
        assert stats["total_tokens_saved"] == 150
    
    def test_calculate_experiment_stats(self):
        """Test experiment statistics calculation."""
        calculator = StatisticsCalculator()
        
        results = [
            ExperimentResult(
                experiment_name="test1", model_name="starcoder",
                original_query="test query", processed_query="test query",
                response="test response", input_tokens=50, output_tokens=50,
                total_tokens=100, response_time=1.0, compression_applied=False,
                compression_result=None, timestamp=datetime.now()
            ),
            ExperimentResult(
                experiment_name="test2", model_name="starcoder",
                original_query="test query 2", processed_query="test query 2",
                response="", input_tokens=0, output_tokens=0,
                total_tokens=0, response_time=0.0, compression_applied=False,
                compression_result=None, timestamp=datetime.now()
            ),
        ]
        
        stats = calculator.calculate_experiment_stats(results)
        assert stats["total_experiments"] == 2
        assert stats["successful_experiments"] == 1  # Only one has non-empty response
        assert stats["failed_experiments"] == 1
        assert stats["success_rate"] == 0.5
    
    def test_calculate_summary_statistics(self):
        """Test summary statistics calculation."""
        calculator = StatisticsCalculator()
        
        values = [1, 2, 3, 4, 5]
        summary = calculator.calculate_summary_statistics(values)
        
        assert summary.count == 5
        assert summary.mean == 3.0
        assert summary.median == 3.0
        assert summary.min_value == 1
        assert summary.max_value == 5


class TestStatisticsReporter:
    """Test StatisticsReporter functionality."""
    
    def test_generate_summary_report(self):
        """Test summary report generation."""
        calculator = StatisticsCalculator()
        reporter = StatisticsReporter(calculator)
        
        results = [
            ExperimentResult(
                experiment_name="test1", model_name="starcoder",
                original_query="test query", processed_query="test query",
                response="test response", input_tokens=50, output_tokens=50,
                total_tokens=100, response_time=1.0, compression_applied=False,
                compression_result=None, timestamp=datetime.now()
            ),
        ]
        
        report = reporter.generate_summary_report(results)
        assert "Experiment Summary Report" in report
        assert "Total Experiments: 1" in report
    
    def test_generate_model_comparison_report(self):
        """Test model comparison report generation."""
        calculator = StatisticsCalculator()
        reporter = StatisticsReporter(calculator)
        
        results = [
            ExperimentResult(
                experiment_name="test1", model_name="starcoder",
                original_query="test query", processed_query="test query",
                response="test response", input_tokens=50, output_tokens=50,
                total_tokens=100, response_time=1.0, compression_applied=False,
                compression_result=None, timestamp=datetime.now()
            ),
        ]
        
        report = reporter.generate_model_comparison_report(results)
        assert "Model Comparison Report" in report
        assert "starcoder" in report


class TestTextFormatter:
    """Test TextFormatter functionality."""
    
    def test_format_title(self):
        """Test title formatting."""
        formatter = TextFormatter()
        title = formatter.format_title("Test Title")
        assert "Test Title" in title
        assert "=" in title
    
    def test_format_section(self):
        """Test section formatting."""
        formatter = TextFormatter()
        section = formatter.format_section("Test Section")
        assert "Test Section" in section
        assert "-" in section
    
    def test_format_key_value(self):
        """Test key-value formatting."""
        formatter = TextFormatter()
        kv = formatter.format_key_value("key", "value")
        assert "key: value" in kv
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        formatter = TextFormatter()
        percent = formatter.format_percentage(0.5)
        assert "50.00%" in percent
    
    def test_format_number(self):
        """Test number formatting."""
        formatter = TextFormatter()
        number = formatter.format_number(123.456, "ms")
        assert "123.46ms" in number
    
    def test_format_duration(self):
        """Test duration formatting."""
        formatter = TextFormatter()
        
        assert "500ms" in formatter.format_duration(0.5)
        assert "1.50s" in formatter.format_duration(1.5)
        assert "1m 30.0s" in formatter.format_duration(90)
    
    def test_format_table(self):
        """Test table formatting."""
        formatter = TextFormatter()
        
        headers = ["Name", "Value"]
        rows = [["Test", "123"], ["Another", "456"]]
        
        table = formatter.format_table(headers, rows)
        assert "Name" in table
        assert "Value" in table
        assert "Test" in table
        assert "Another" in table
    
    def test_format_list(self):
        """Test list formatting."""
        formatter = TextFormatter()
        
        items = ["Item 1", "Item 2", "Item 3"]
        formatted_list = formatter.format_list(items)
        
        assert "Item 1" in formatted_list
        assert "Item 2" in formatted_list
        assert "Item 3" in formatted_list
    
    def test_wrap_text(self):
        """Test text wrapping."""
        formatter = TextFormatter()
        
        long_text = "This is a very long text that should be wrapped to fit within the specified width."
        wrapped = formatter.wrap_text(long_text, 20)
        
        lines = wrapped.split('\n')
        for line in lines:
            assert len(line) <= 20


class TestConsoleFormatter:
    """Test ConsoleFormatter functionality."""
    
    def test_colorize(self):
        """Test text colorization."""
        formatter = ConsoleFormatter()
        
        colored = formatter.colorize("test", "red")
        # In test environment, colors might not be applied
        assert "test" in colored
    
    def test_format_success(self):
        """Test success formatting."""
        formatter = ConsoleFormatter()
        success_text = formatter.format_success("Success!")
        assert "Success!" in success_text
    
    def test_format_error(self):
        """Test error formatting."""
        formatter = ConsoleFormatter()
        error_text = formatter.format_error("Error!")
        assert "Error!" in error_text
    
    def test_format_warning(self):
        """Test warning formatting."""
        formatter = ConsoleFormatter()
        warning_text = formatter.format_warning("Warning!")
        assert "Warning!" in warning_text
    
    def test_format_info(self):
        """Test info formatting."""
        formatter = ConsoleFormatter()
        info_text = formatter.format_info("Info!")
        assert "Info!" in info_text
    
    def test_format_highlight(self):
        """Test highlight formatting."""
        formatter = ConsoleFormatter()
        highlight_text = formatter.format_highlight("Highlight!")
        assert "Highlight!" in highlight_text


class TestRetryHandler:
    """Test RetryHandler functionality."""
    
    def test_retry_config_creation(self):
        """Test retry config creation."""
        config = RetryConfig(max_attempts=5, base_delay=2.0)
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.strategy == RetryStrategy.EXPONENTIAL
    
    def test_should_retry(self):
        """Test retry decision logic."""
        config = RetryConfig(max_attempts=3)
        handler = RetryHandler(config)
        
        # Should retry on retryable exception
        assert handler.should_retry(ConnectionError(), 0) is True
        assert handler.should_retry(TimeoutError(), 1) is True
        
        # Should not retry on last attempt
        assert handler.should_retry(ConnectionError(), 2) is False
        
        # Should not retry on non-retryable exception
        assert handler.should_retry(ValueError(), 0) is False
    
    def test_get_delay(self):
        """Test delay calculation."""
        config = RetryConfig(base_delay=1.0, strategy=RetryStrategy.FIXED)
        handler = RetryHandler(config)
        
        # With jitter, the delay will be slightly different each time
        delay = handler.get_delay(0)
        assert 0.5 <= delay <= 1.5  # Allow for jitter variation
        
        # Test exponential backoff with jitter
        delay_exp = handler.get_delay(1)
        assert delay_exp > 0  # Should be positive
        
        config.strategy = RetryStrategy.EXPONENTIAL
        handler = RetryHandler(config)
        
        # With exponential strategy and jitter
        delay_exp = handler.get_delay(0)
        assert 0.5 <= delay_exp <= 1.5  # Allow for jitter variation
        
        # Test exponential backoff (with jitter)
        delay_exp_1 = handler.get_delay(1)
        assert delay_exp_1 > 1.0  # Should be exponential
        delay_exp_2 = handler.get_delay(2)
        # With jitter, we can't guarantee strict ordering, but both should be positive
        assert delay_exp_1 > 0 and delay_exp_2 > 0
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test successful execution with retry."""
        config = RetryConfig(max_attempts=3)
        handler = RetryHandler(config)
        
        async def success_func():
            return "success"
        
        result = await handler.execute_with_retry(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_failure(self):
        """Test failed execution with retry."""
        config = RetryConfig(max_attempts=3)
        handler = RetryHandler(config)
        
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Connection failed")
        
        with pytest.raises(ConnectionError):
            await handler.execute_with_retry(failing_func)
        
        assert call_count == 3  # Should retry 3 times


class TestCircuitBreaker:
    """Test CircuitBreaker functionality."""
    
    def test_circuit_breaker_config_creation(self):
        """Test circuit breaker config creation."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0)
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 30.0
        assert config.success_threshold == 3
    
    def test_initial_state(self):
        """Test initial circuit breaker state."""
        breaker = CircuitBreaker()
        assert breaker.is_closed()
        assert not breaker.is_open()
        assert not breaker.is_half_open()
    
    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test successful call through circuit breaker."""
        breaker = CircuitBreaker()
        
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.is_closed()
    
    @pytest.mark.asyncio
    async def test_failure_threshold(self):
        """Test circuit breaker opening after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker(config)
        
        async def failing_func():
            raise ConnectionError("Connection failed")
        
        # First failure
        with pytest.raises(ConnectionError):
            await breaker.call(failing_func)
        assert breaker.is_closed()
        
        # Second failure - should open circuit
        with pytest.raises(ConnectionError):
            await breaker.call(failing_func)
        assert breaker.is_open()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_error(self):
        """Test circuit breaker open error."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker(config)
        
        async def failing_func():
            raise ConnectionError("Connection failed")
        
        # Trigger circuit breaker to open
        with pytest.raises(ConnectionError):
            await breaker.call(failing_func)
        
        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(failing_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1, success_threshold=1)
        breaker = CircuitBreaker(config)
        
        async def failing_func():
            raise ConnectionError("Connection failed")
        
        async def success_func():
            return "success"
        
        # Trigger circuit breaker to open
        with pytest.raises(ConnectionError):
            await breaker.call(failing_func)
        
        assert breaker.is_open()
        
        # Wait for recovery timeout
        await asyncio.sleep(0.2)
        
        # Should be half-open now
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.is_closed()


class TestResilientClient:
    """Test ResilientClient functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful execution."""
        client = ResilientClient()
        
        async def success_func():
            return "success"
        
        result = await client.execute(success_func)
        assert result == "success"
        assert client.is_closed()
    
    @pytest.mark.asyncio
    async def test_execution_with_retry(self):
        """Test execution with retry."""
        retry_config = RetryConfig(max_attempts=2)
        client = ResilientClient(retry_config=retry_config)
        
        call_count = 0
        
        async def eventually_successful_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await client.execute(eventually_successful_func)
        assert result == "success"
        assert call_count == 2
    
    def test_circuit_breaker_state(self):
        """Test circuit breaker state access."""
        client = ResilientClient()
        assert client.get_circuit_breaker_state() == CircuitBreakerState.CLOSED
        assert client.get_failure_count() == 0
    
    def test_reset_circuit_breaker(self):
        """Test circuit breaker reset."""
        client = ResilientClient()
        client.reset_circuit_breaker()
        assert client.get_circuit_breaker_state() == CircuitBreakerState.CLOSED
        assert client.get_failure_count() == 0
