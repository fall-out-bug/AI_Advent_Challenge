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
            "token_counter": {"mode": "simple", "limit_profile": "practical"},
            "ml_service": {"url": "http://localhost:8004"},
        }
        self.bootstrapper = ApplicationBootstrapper(self.config)

    def test_create_token_counter(self):
        """Test token counter creation via DI container."""
        # Bootstrap the application to get the container
        context = self.bootstrapper.bootstrap()
        
        # Get token counter from container
        token_counter = self.bootstrapper.container.token_counter()
        
        # Verify it's a proper token counter
        assert hasattr(token_counter, "count_tokens")
        assert hasattr(token_counter, "get_model_limits")
        assert hasattr(token_counter, "check_limit_exceeded")
        assert hasattr(token_counter, "estimate_compression_target")

    def test_create_text_compressor(self):
        """Test text compressor creation via DI container."""
        # Bootstrap the application to get the container
        context = self.bootstrapper.bootstrap()
        
        # Get text compressor from container
        text_compressor = self.bootstrapper.container.text_compressor()
        
        # Verify it's a proper text compressor
        assert hasattr(text_compressor, "compress_by_truncation")
        assert hasattr(text_compressor, "compress_by_keywords")
        assert hasattr(text_compressor, "compress_text")

    def test_create_ml_client(self):
        """Test ML client creation via DI container."""
        # Bootstrap the application to get the container
        context = self.bootstrapper.bootstrap()
        
        # Get ML client from container
        ml_client = self.bootstrapper.container.ml_client()
        
        # Verify it's a proper ML client
        assert hasattr(ml_client, "make_request")
        assert hasattr(ml_client, "count_tokens")

    def test_create_experiments(self):
        """Test experiments creation via DI container."""
        # Bootstrap the application to get the container
        context = self.bootstrapper.bootstrap()
        
        # Get experiments from container
        experiments = self.bootstrapper.container.experiments()
        
        # Verify it's a proper experiments instance
        assert hasattr(experiments, "run_limit_exceeded_experiment")
        assert hasattr(experiments, "run_model_comparison_experiment")

    def test_create_reporter(self):
        """Test reporter creation via DI container."""
        # Bootstrap the application to get the container
        context = self.bootstrapper.bootstrap()
        
        # Get reporter from container
        reporter = self.bootstrapper.container.application_context().reporter
        
        # Verify it's a proper reporter
        assert hasattr(reporter, "print_experiment_summary")
        assert hasattr(reporter, "print_detailed_analysis")

    def test_bootstrap_success(self):
        """Test successful bootstrap."""
        # Bootstrap the application
        context = self.bootstrapper.bootstrap()
        
        # Verify context is created
        assert context is not None
        assert hasattr(context, "validate_components")
        
        # Verify container is initialized
        assert self.bootstrapper.container is not None
        
        # Verify all components are available
        assert self.bootstrapper.container.token_counter() is not None
        assert self.bootstrapper.container.text_compressor() is not None
        assert self.bootstrapper.container.ml_client() is not None
        assert self.bootstrapper.container.experiments() is not None
        assert self.bootstrapper.container.application_context() is not None

    @patch("core.bootstrap.application_bootstrapper.ApplicationContext")
    @patch("core.bootstrap.application_bootstrapper.configure_container")
    def test_bootstrap_validation_failure(
        self,
        mock_configure_container,
        mock_context_class,
    ):
        """Test bootstrap with validation failure."""
        # Setup mocks
        mock_context = Mock()
        mock_context.validate_components.return_value = False
        mock_context_class.return_value = mock_context
        
        # Mock container to return the failing context
        mock_container = Mock()
        mock_container.application_context.return_value = mock_context
        mock_configure_container.return_value = mock_container

        # Execute bootstrap and expect exception
        with pytest.raises(
            BootstrapError, match="Failed to validate application components"
        ):
            self.bootstrapper.bootstrap()

    @patch("core.bootstrap.application_bootstrapper.configure_container")
    def test_bootstrap_component_creation_failure(self, mock_configure_container):
        """Test bootstrap with component creation failure."""
        # Setup mock to raise exception
        mock_configure_container.side_effect = Exception("Container initialization failed")

        # Execute bootstrap and expect exception
        with pytest.raises(BootstrapError, match="Failed to bootstrap application"):
            self.bootstrapper.bootstrap()

    def test_get_bootstrap_info(self):
        """Test getting bootstrap information."""
        info = self.bootstrapper.get_bootstrap_info()

        assert "config_keys" in info
        assert "config_available" in info
        assert "logger_configured" in info
        assert "container_initialized" in info
        assert info["config_available"] is True
        assert info["logger_configured"] is True


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
