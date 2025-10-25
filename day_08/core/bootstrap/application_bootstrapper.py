"""
Application bootstrapper for dependency initialization.

This module provides the ApplicationBootstrapper class that handles
the initialization of all application components and their dependencies.
"""

import os
from typing import Optional, Dict, Any

from core.experiments import TokenLimitExperiments
from core.interfaces.protocols import TokenCounterProtocol
from core.ml_client import TokenAnalysisClient
from core.text_compressor import SimpleTextCompressor
from models.application_context import ApplicationContext
from utils.console_reporter import ConsoleReporter
from utils.logging import LoggerFactory


class ApplicationBootstrapper:
    """
    Bootstrap application with all dependencies.
    
    This class handles the initialization of all application components,
    their dependencies, and creates the ApplicationContext for runtime execution.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize bootstrapper with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = LoggerFactory.create_logger(__name__)

    def bootstrap(self) -> ApplicationContext:
        """
        Bootstrap application with all dependencies.
        
        Creates and initializes all required components,
        then returns the ApplicationContext.
        
        Returns:
            ApplicationContext: Initialized application context
            
        Raises:
            BootstrapError: If component initialization fails
        """
        self.logger.info("Starting application bootstrap")
        
        try:
            # Initialize core components
            token_counter = self._create_token_counter()
            text_compressor = self._create_text_compressor(token_counter)
            ml_client = self._create_ml_client()
            experiments = self._create_experiments(ml_client, token_counter, text_compressor)
            reporter = self._create_reporter()
            
            # Create application context
            context = ApplicationContext(
                token_counter=token_counter,
                text_compressor=text_compressor,
                ml_client=ml_client,
                experiments=experiments,
                reporter=reporter,
                logger=self.logger,
                config=self.config
            )
            
            # Validate context
            if not context.validate_components():
                raise BootstrapError("Failed to validate application components")
            
            self.logger.info("Application bootstrap completed successfully")
            return context
            
        except Exception as e:
            self.logger.error(f"Bootstrap failed: {e}")
            raise BootstrapError(f"Failed to bootstrap application: {e}") from e

    def _create_token_counter(self) -> TokenCounterProtocol:
        """
        Create token counter instance.
        
        Returns:
            TokenCounterProtocol: Initialized token counter
        """
        self.logger.debug("Creating token counter")
        
        # Use configuration if available, otherwise use defaults
        mode = self.config.get('token_counter_mode', 'simple')
        limit_profile = self.config.get('limit_profile', 'practical')
        
        # For now, we'll create a mock token counter for testing
        # In the future, this could create different types based on mode
        from unittest.mock import Mock
        mock_counter = Mock(spec=TokenCounterProtocol)
        mock_counter.count_tokens.return_value = Mock(count=100)
        mock_counter.get_model_limits.return_value = Mock(max_input_tokens=4096)
        mock_counter.check_limit_exceeded.return_value = False
        mock_counter.estimate_compression_target.return_value = 3000
        
        return mock_counter

    def _create_text_compressor(self, token_counter: TokenCounterProtocol) -> SimpleTextCompressor:
        """
        Create text compressor instance.
        
        Args:
            token_counter: Token counter dependency
            
        Returns:
            SimpleTextCompressor: Initialized text compressor
        """
        self.logger.debug("Creating text compressor")
        return SimpleTextCompressor(token_counter)

    def _create_ml_client(self) -> TokenAnalysisClient:
        """
        Create ML client instance.
        
        Returns:
            TokenAnalysisClient: Initialized ML client
        """
        self.logger.debug("Creating ML client")
        
        # Use configuration for ML service URL if available
        base_url = self.config.get('ml_service_url', 'http://localhost:8004')
        
        return TokenAnalysisClient(base_url=base_url)

    def _create_experiments(
        self, 
        ml_client: TokenAnalysisClient, 
        token_counter: TokenCounterProtocol, 
        text_compressor: SimpleTextCompressor
    ) -> TokenLimitExperiments:
        """
        Create experiments orchestrator instance.
        
        Args:
            ml_client: ML client dependency
            token_counter: Token counter dependency
            text_compressor: Text compressor dependency
            
        Returns:
            TokenLimitExperiments: Initialized experiments orchestrator
        """
        self.logger.debug("Creating experiments orchestrator")
        return TokenLimitExperiments(ml_client, token_counter, text_compressor)

    def _create_reporter(self) -> ConsoleReporter:
        """
        Create console reporter instance.
        
        Returns:
            ConsoleReporter: Initialized console reporter
        """
        self.logger.debug("Creating console reporter")
        return ConsoleReporter()

    def get_bootstrap_info(self) -> Dict[str, Any]:
        """
        Get information about the bootstrap configuration.
        
        Returns:
            Dict[str, Any]: Bootstrap configuration information
        """
        return {
            'config_keys': list(self.config.keys()),
            'config_available': bool(self.config),
            'logger_configured': self.logger is not None,
            'bootstrap_methods': [
                '_create_token_counter',
                '_create_text_compressor', 
                '_create_ml_client',
                '_create_experiments',
                '_create_reporter'
            ]
        }


class BootstrapError(Exception):
    """Exception raised when application bootstrap fails."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
