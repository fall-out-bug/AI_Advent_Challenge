"""
Application bootstrapper for dependency initialization.

This module provides the ApplicationBootstrapper class that handles
the initialization of all application components and their dependencies
using the DI container.
"""

import os
from typing import Any, Dict, Optional

from core.container import ApplicationContainer, configure_container, get_container
from core.experiments import TokenLimitExperiments
from core.interfaces.protocols import TokenCounterProtocol
from core.ml_client import TokenAnalysisClient
from core.text_compressor import SimpleTextCompressor
from models.application_context import ApplicationContext
from utils.console_reporter import ConsoleReporter
from utils.logging import LoggerFactory


class ApplicationBootstrapper:
    """
    Bootstrap application with all dependencies using DI container.

    This class handles the initialization of all application components,
    their dependencies, and creates the ApplicationContext for runtime execution
    using the dependency injection container.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize bootstrapper with configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = LoggerFactory.create_logger(__name__)
        self.container: Optional[ApplicationContainer] = None

    def bootstrap(self) -> ApplicationContext:
        """
        Bootstrap application with all dependencies using DI container.

        Creates and initializes all required components using the DI container,
        then returns the ApplicationContext.

        Returns:
            ApplicationContext: Initialized application context

        Raises:
            BootstrapError: If component initialization fails
        """
        self.logger.info("Starting application bootstrap with DI container")

        try:
            # Configure and initialize DI container
            self.container = configure_container(self.config)

            # Get application context from container
            context = self.container.application_context()

            # Validate context
            if not context.validate_components():
                raise BootstrapError("Failed to validate application components")

            self.logger.info("Application bootstrap completed successfully")
            return context

        except Exception as e:
            self.logger.error(f"Bootstrap failed: {e}")
            raise BootstrapError(f"Failed to bootstrap application: {e}") from e

    def get_bootstrap_info(self) -> Dict[str, Any]:
        """
        Get information about the bootstrap configuration.

        Returns:
            Dict[str, Any]: Bootstrap configuration information
        """
        return {
            "config_keys": list(self.config.keys()),
            "config_available": bool(self.config),
            "logger_configured": self.logger is not None,
            "container_initialized": self.container is not None,
            "container_health": self._check_container_health()
            if self.container
            else None,
        }

    def _check_container_health(self) -> Dict[str, Any]:
        """
        Check container health.

        Returns:
            Dict[str, Any]: Container health information
        """
        if not self.container:
            return {"status": "not_initialized"}

        try:
            # Test if we can get components from container
            token_counter = self.container.token_counter()
            text_compressor = self.container.text_compressor()
            ml_client = self.container.ml_client()

            return {
                "status": "healthy",
                "components": {
                    "token_counter": token_counter is not None,
                    "text_compressor": text_compressor is not None,
                    "ml_client": ml_client is not None,
                },
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def get_container(self) -> Optional[ApplicationContainer]:
        """
        Get the DI container instance.

        Returns:
            Optional[ApplicationContainer]: Container instance if initialized
        """
        return self.container


class BootstrapError(Exception):
    """Exception raised when application bootstrap fails."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
