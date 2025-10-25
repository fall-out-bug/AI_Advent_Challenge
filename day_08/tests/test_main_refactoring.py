"""
Tests for main.py refactoring.

This module tests the refactored main components:
ApplicationContext, ApplicationBootstrapper, and run.py functionality.
"""

import asyncio
import os
import sys
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from core.bootstrap.application_bootstrapper import (
    ApplicationBootstrapper,
    BootstrapError,
)
from core.experiments import TokenLimitExperiments
from core.interfaces.protocols import TokenCounterProtocol
from core.ml_client import TokenAnalysisClient
from core.text_compressor import SimpleTextCompressor
from models.application_context import ApplicationContext
from utils.console_reporter import ConsoleReporter
from utils.logging import LoggerFactory


class TestApplicationContext:
    """Test ApplicationContext functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_token_counter = Mock(spec=TokenCounterProtocol)
        self.mock_text_compressor = Mock(spec=SimpleTextCompressor)
        self.mock_ml_client = Mock(spec=TokenAnalysisClient)
        self.mock_experiments = Mock(spec=TokenLimitExperiments)
        self.mock_reporter = Mock(spec=ConsoleReporter)
        self.mock_logger = Mock()

        self.context = ApplicationContext(
            token_counter=self.mock_token_counter,
            text_compressor=self.mock_text_compressor,
            ml_client=self.mock_ml_client,
            experiments=self.mock_experiments,
            reporter=self.mock_reporter,
            logger=self.mock_logger,
            config={"test": "value"},
        )

    def test_initialization(self):
        """Test ApplicationContext initialization."""
        assert self.context.token_counter == self.mock_token_counter
        assert self.context.text_compressor == self.mock_text_compressor
        assert self.context.ml_client == self.mock_ml_client
        assert self.context.experiments == self.mock_experiments
        assert self.context.reporter == self.mock_reporter
        assert self.context.logger == self.mock_logger
        assert self.context.config == {"test": "value"}

    def test_get_component_status(self):
        """Test getting component status."""
        status = self.context.get_component_status()

        assert "token_counter" in status
        assert "text_compressor" in status
        assert "ml_client" in status
        assert "experiments" in status
        assert "reporter" in status
        assert "logger" in status
        assert "config_available" in status
        assert status["config_available"] is True

    def test_validate_components(self):
        """Test component validation."""
        assert self.context.validate_components() is True

        # Test with None component
        self.context.token_counter = None
        assert self.context.validate_components() is False

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup functionality."""
        # Mock async close methods
        self.mock_ml_client.close = AsyncMock()
        self.mock_token_counter.close = AsyncMock()

        await self.context.cleanup()

        # Verify close methods were called
        self.mock_ml_client.close.assert_called_once()
        self.mock_token_counter.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_with_error(self):
        """Test cleanup with error handling."""
        # Mock close method that raises exception
        self.mock_ml_client.close = AsyncMock(side_effect=Exception("Close error"))

        # Should not raise exception
        await self.context.cleanup()

        # Verify error was logged
        self.mock_logger.error.assert_called()

    def test_get_summary(self):
        """Test getting context summary."""
        summary = self.context.get_summary()

        assert "Application Context Summary" in summary
        assert "Token Counter" in summary
        assert "Text Compressor" in summary
        assert "ML Client" in summary
        assert "Experiments" in summary
        assert "Reporter" in summary
        assert "Logger" in summary
        assert "Config Available" in summary
        assert "Components Valid" in summary


class TestApplicationBootstrapper:
    """Test ApplicationBootstrapper functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "token_counter_mode": "simple",
            "limit_profile": "practical",
            "ml_service_url": "http://localhost:8004",
        }
        self.bootstrapper = ApplicationBootstrapper(self.config)

    def test_create_token_counter(self):
        """Test token counter creation."""
        result = self.bootstrapper._create_token_counter()

        # Verify it's a mock with the right spec
        assert hasattr(result, "count_tokens")
        assert hasattr(result, "get_model_limits")
        assert hasattr(result, "check_limit_exceeded")
        assert hasattr(result, "estimate_compression_target")

    @patch("core.bootstrap.application_bootstrapper.SimpleTextCompressor")
    def test_create_text_compressor(self, mock_compressor_class):
        """Test text compressor creation."""
        mock_instance = Mock()
        mock_compressor_class.return_value = mock_instance
        mock_token_counter = Mock()

        result = self.bootstrapper._create_text_compressor(mock_token_counter)

        assert result == mock_instance
        mock_compressor_class.assert_called_once_with(mock_token_counter)

    @patch("core.bootstrap.application_bootstrapper.TokenAnalysisClient")
    def test_create_ml_client(self, mock_client_class):
        """Test ML client creation."""
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance

        result = self.bootstrapper._create_ml_client()

        assert result == mock_instance
        mock_client_class.assert_called_once_with(base_url="http://localhost:8004")

    @patch("core.bootstrap.application_bootstrapper.TokenLimitExperiments")
    def test_create_experiments(self, mock_experiments_class):
        """Test experiments creation."""
        mock_instance = Mock()
        mock_experiments_class.return_value = mock_instance
        mock_ml_client = Mock()
        mock_token_counter = Mock()
        mock_text_compressor = Mock()

        result = self.bootstrapper._create_experiments(
            mock_ml_client, mock_token_counter, mock_text_compressor
        )

        assert result == mock_instance
        mock_experiments_class.assert_called_once_with(
            mock_ml_client, mock_token_counter, mock_text_compressor
        )

    @patch("core.bootstrap.application_bootstrapper.ConsoleReporter")
    def test_create_reporter(self, mock_reporter_class):
        """Test reporter creation."""
        mock_instance = Mock()
        mock_reporter_class.return_value = mock_instance

        result = self.bootstrapper._create_reporter()

        assert result == mock_instance
        mock_reporter_class.assert_called_once()

    @patch("core.bootstrap.application_bootstrapper.ApplicationContext")
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_reporter"
    )
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_experiments"
    )
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_ml_client"
    )
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_text_compressor"
    )
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_token_counter"
    )
    def test_bootstrap_success(
        self,
        mock_create_token_counter,
        mock_create_text_compressor,
        mock_create_ml_client,
        mock_create_experiments,
        mock_create_reporter,
        mock_context_class,
    ):
        """Test successful bootstrap."""
        # Setup mocks
        mock_token_counter = Mock()
        mock_text_compressor = Mock()
        mock_ml_client = Mock()
        mock_experiments = Mock()
        mock_reporter = Mock()
        mock_context = Mock()

        mock_create_token_counter.return_value = mock_token_counter
        mock_create_text_compressor.return_value = mock_text_compressor
        mock_create_ml_client.return_value = mock_ml_client
        mock_create_experiments.return_value = mock_experiments
        mock_create_reporter.return_value = mock_reporter
        mock_context_class.return_value = mock_context
        mock_context.validate_components.return_value = True

        # Execute bootstrap
        result = self.bootstrapper.bootstrap()

        # Verify result
        assert result == mock_context

        # Verify all create methods were called
        mock_create_token_counter.assert_called_once()
        mock_create_text_compressor.assert_called_once_with(mock_token_counter)
        mock_create_ml_client.assert_called_once()
        mock_create_experiments.assert_called_once_with(
            mock_ml_client, mock_token_counter, mock_text_compressor
        )
        mock_create_reporter.assert_called_once()

        # Verify context was created with correct parameters
        mock_context_class.assert_called_once_with(
            token_counter=mock_token_counter,
            text_compressor=mock_text_compressor,
            ml_client=mock_ml_client,
            experiments=mock_experiments,
            reporter=mock_reporter,
            logger=self.bootstrapper.logger,
            config=self.config,
        )

    @patch("core.bootstrap.application_bootstrapper.ApplicationContext")
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_reporter"
    )
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_experiments"
    )
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_ml_client"
    )
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_text_compressor"
    )
    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_token_counter"
    )
    def test_bootstrap_validation_failure(
        self,
        mock_create_token_counter,
        mock_create_text_compressor,
        mock_create_ml_client,
        mock_create_experiments,
        mock_create_reporter,
        mock_context_class,
    ):
        """Test bootstrap with validation failure."""
        # Setup mocks
        mock_context = Mock()
        mock_context.validate_components.return_value = False
        mock_context_class.return_value = mock_context

        # Execute bootstrap and expect exception
        with pytest.raises(
            BootstrapError, match="Failed to validate application components"
        ):
            self.bootstrapper.bootstrap()

    @patch(
        "core.bootstrap.application_bootstrapper.ApplicationBootstrapper._create_token_counter"
    )
    def test_bootstrap_component_creation_failure(self, mock_create_token_counter):
        """Test bootstrap with component creation failure."""
        # Setup mock to raise exception
        mock_create_token_counter.side_effect = Exception("Creation failed")

        # Execute bootstrap and expect exception
        with pytest.raises(BootstrapError, match="Failed to bootstrap application"):
            self.bootstrapper.bootstrap()

    def test_get_bootstrap_info(self):
        """Test getting bootstrap information."""
        info = self.bootstrapper.get_bootstrap_info()

        assert "config_keys" in info
        assert "config_available" in info
        assert "logger_configured" in info
        assert "bootstrap_methods" in info
        assert info["config_available"] is True
        assert info["logger_configured"] is True
        assert len(info["bootstrap_methods"]) == 5


class TestRunPy:
    """Test run.py functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock(spec=ApplicationContext)
        self.mock_context.logger = Mock()
        self.mock_context.ml_client = Mock()
        self.mock_context.experiments = Mock()
        self.mock_context.reporter = Mock()

    @pytest.mark.asyncio
    async def test_run_experiments_success(self):
        """Test successful experiment execution."""
        # Setup mocks
        self.mock_context.ml_client.check_availability = AsyncMock(return_value=True)
        self.mock_context.experiments.run_limit_exceeded_experiment = AsyncMock(
            return_value=[Mock()]
        )
        self.mock_context.experiments.get_experiment_summary = Mock(
            return_value={
                "total_experiments": 3,
                "successful_experiments": 2,
                "success_rate": 0.67,
                "avg_response_time": 1.5,
                "total_tokens_used": 1500,
            }
        )

        # Import and run
        from run import run_experiments

        await run_experiments(self.mock_context)

        # Verify calls
        self.mock_context.ml_client.check_availability.assert_called_once_with(
            "starcoder"
        )
        self.mock_context.experiments.run_limit_exceeded_experiment.assert_called_once_with(
            "starcoder"
        )

    @pytest.mark.asyncio
    async def test_run_experiments_starcoder_unavailable(self):
        """Test experiment execution when StarCoder is unavailable."""
        # Setup mocks
        self.mock_context.ml_client.check_availability = AsyncMock(return_value=False)

        # Import and run
        from run import run_experiments

        await run_experiments(self.mock_context)

        # Verify availability check was made
        self.mock_context.ml_client.check_availability.assert_called_once_with(
            "starcoder"
        )
        # Verify experiments were not run
        self.mock_context.experiments.run_limit_exceeded_experiment.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_demo_success(self):
        """Test successful demo execution."""
        # Setup mocks
        self.mock_context.ml_client.check_availability = AsyncMock(return_value=True)
        self.mock_context.experiments.run_short_query_experiment = AsyncMock(
            return_value=[Mock()]
        )

        # Import and run
        from run import run_demo

        await run_demo(self.mock_context)

        # Verify calls
        self.mock_context.ml_client.check_availability.assert_called_once_with(
            "starcoder"
        )
        self.mock_context.experiments.run_short_query_experiment.assert_called_once_with(
            "starcoder"
        )

    @pytest.mark.asyncio
    async def test_run_comparison_success(self):
        """Test successful model comparison execution."""
        # Setup mocks
        self.mock_context.ml_client.check_availability = AsyncMock(return_value=True)
        self.mock_context.experiments.run_model_comparison_experiment = AsyncMock(
            return_value=[Mock()]
        )

        # Import and run
        from run import run_comparison

        await run_comparison(self.mock_context)

        # Verify calls
        self.mock_context.ml_client.check_availability.assert_called_once_with(
            "starcoder"
        )
        self.mock_context.experiments.run_model_comparison_experiment.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_advanced_compression_success(self):
        """Test successful advanced compression execution."""
        # Setup mocks
        self.mock_context.experiments.run_advanced_compression_experiment = AsyncMock(
            return_value=[Mock()]
        )

        # Import and run
        from run import run_advanced_compression

        await run_advanced_compression(self.mock_context)

        # Verify calls
        self.mock_context.experiments.run_advanced_compression_experiment.assert_called_once()

    def test_load_config(self):
        """Test configuration loading."""
        # Import and test
        from run import load_config

        with patch.dict(
            os.environ,
            {
                "TOKEN_COUNTER_MODE": "hybrid",
                "LIMIT_PROFILE": "theoretical",
                "ML_SERVICE_URL": "http://test:8004",
                "LOG_LEVEL": "DEBUG",
                "DEBUG": "true",
            },
        ):
            config = load_config()

            assert config["token_counter_mode"] == "hybrid"
            assert config["limit_profile"] == "theoretical"
            assert config["ml_service_url"] == "http://test:8004"
            assert config["log_level"] == "DEBUG"
            assert config["debug"] is True

    def test_get_experiment_type(self):
        """Test experiment type determination."""
        from run import _get_experiment_type

        # Test with no arguments
        with patch("sys.argv", ["run.py"]):
            assert _get_experiment_type() == "full"

        # Test with demo argument
        with patch("sys.argv", ["run.py", "--demo"]):
            assert _get_experiment_type() == "demo"

        # Test with comparison argument
        with patch("sys.argv", ["run.py", "--comparison"]):
            assert _get_experiment_type() == "comparison"

        # Test with advanced argument
        with patch("sys.argv", ["run.py", "--advanced"]):
            assert _get_experiment_type() == "advanced"

    @pytest.mark.asyncio
    async def test_run_experiment_dispatch(self):
        """Test experiment type dispatch."""
        from run import _run_experiment

        # Test demo dispatch
        with patch("run.run_demo") as mock_run_demo:
            await _run_experiment(self.mock_context, "demo")
            mock_run_demo.assert_called_once_with(self.mock_context)

        # Test comparison dispatch
        with patch("run.run_comparison") as mock_run_comparison:
            await _run_experiment(self.mock_context, "comparison")
            mock_run_comparison.assert_called_once_with(self.mock_context)

        # Test advanced dispatch
        with patch("run.run_advanced_compression") as mock_run_advanced:
            await _run_experiment(self.mock_context, "advanced")
            mock_run_advanced.assert_called_once_with(self.mock_context)

        # Test full dispatch
        with patch("run.run_experiments") as mock_run_experiments:
            await _run_experiment(self.mock_context, "full")
            mock_run_experiments.assert_called_once_with(self.mock_context)


class TestBootstrapError:
    """Test BootstrapError exception."""

    def test_bootstrap_error_creation(self):
        """Test BootstrapError creation."""
        error = BootstrapError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
