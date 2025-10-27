"""
Dependency Injection Container for the Token Analysis System.

This module defines the ApplicationContainer using dependency-injector library
to manage all application dependencies and their lifecycle.
"""

from typing import Any, Dict, Optional

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from api.handlers.token_handler import TokenServiceHandler
from core.compressors.strategy import CompressionStrategyFactory
from core.experiments import TokenLimitExperiments
from core.factories.token_counter_factory import TokenCounterFactory
from core.interfaces.protocols import (
    ConfigurationProtocol,
    TokenCounterProtocol,
)
from core.ml_client import TokenAnalysisClient
from core.text_compressor import SimpleTextCompressor
from core.validators.request_validator import RequestValidator
from services.token_service import TokenService
from tests.mocks.mock_config import MockConfiguration
from utils.console_formatter import ConsoleFormatter
from utils.console_reporter import ConsoleReporter
from utils.logging import LoggerFactory
from utils.report_generator import ReportGenerator
from utils.statistics_collector import StatisticsCollector


class ApplicationContainer(containers.DeclarativeContainer):
    """
    Application dependency injection container.

    Manages all application dependencies, their configuration,
    and lifecycle using dependency-injector library.
    """

    # Configuration
    config = providers.Configuration()

    # Logging
    logger_factory = providers.Factory(
        lambda: LoggerFactory  # Return the class itself, not an instance
    )

    # Configuration Protocol Implementation
    configuration = providers.Singleton(
        MockConfiguration  # Using mock for now, can be replaced with real implementation
    )

    # Core Services - Token Counter
    token_counter_factory = providers.Factory(
        lambda: TokenCounterFactory  # Return the class itself
    )

    token_counter = providers.Factory(
        TokenCounterFactory.create_simple, config=configuration
    )

    # Core Services - Text Compressor
    compression_strategy_factory = providers.Factory(
        lambda: CompressionStrategyFactory  # Return the class itself
    )

    text_compressor = providers.Factory(
        SimpleTextCompressor, token_counter=token_counter
    )

    # Core Services - ML Client
    ml_client = providers.Singleton(TokenAnalysisClient, base_url=config.ml_service.url)

    # Core Services - Experiments
    experiments = providers.Factory(
        TokenLimitExperiments,
        model_client=ml_client,
        token_counter=token_counter,
        text_compressor=text_compressor,
    )

    # Validation Layer
    request_validator = providers.Singleton(RequestValidator)

    # Service Layer
    token_service = providers.Factory(
        TokenService,
        token_counter=token_counter,
    )

    # Handler Layer
    token_service_handler = providers.Factory(
        TokenServiceHandler,
        service=token_service,
    )

    # Reporting Components
    statistics_collector = providers.Factory(StatisticsCollector)
    console_formatter = providers.Factory(ConsoleFormatter)
    report_generator = providers.Factory(
        ReportGenerator, collector=statistics_collector, formatter=console_formatter
    )
    console_reporter = providers.Factory(ConsoleReporter)

    # Application Context
    application_context = providers.Factory(
        "models.application_context.ApplicationContext",
        token_counter=token_counter,
        text_compressor=text_compressor,
        ml_client=ml_client,
        experiments=experiments,
        reporter=console_reporter,
        logger=providers.Factory(
            lambda: LoggerFactory.create_logger("ApplicationContext")
        ),
        config=config,
    )


# Global container instance
container = ApplicationContainer()


def configure_container(
    config_dict: Optional[Dict[str, Any]] = None,
) -> ApplicationContainer:
    """
    Configure the application container with provided configuration.

    Args:
        config_dict: Optional configuration dictionary

    Returns:
        ApplicationContainer: Configured container instance
    """
    # Create a new container instance for each configuration
    new_container = ApplicationContainer()

    if config_dict:
        new_container.config.from_dict(config_dict)
    else:
        # Default configuration
        new_container.config.from_dict(
            {
                "ml_service": {"url": "http://localhost:8004"},
                "token_counter": {"mode": "simple", "limit_profile": "practical"},
                "logging": {"level": "INFO", "format": "json"},
            }
        )

    return new_container


def get_container() -> ApplicationContainer:
    """
    Get the global container instance.

    Returns:
        ApplicationContainer: Global container instance
    """
    # Ensure container is properly configured
    if not hasattr(container, "config") or container.config() is None:
        configure_container()
    return container


# Wiring configuration for dependency injection
def wire_modules(modules: list) -> None:
    """
    Wire modules for dependency injection.

    Args:
        modules: List of modules to wire
    """
    container.wire(modules=modules)


def unwire_modules() -> None:
    """Unwire all modules."""
    container.unwire()


# Convenience functions for common dependencies
@inject
def get_token_counter(
    token_counter: TokenCounterProtocol = Provide[ApplicationContainer.token_counter],
) -> TokenCounterProtocol:
    """Get token counter instance."""
    return token_counter


@inject
def get_text_compressor(
    text_compressor: SimpleTextCompressor = Provide[
        ApplicationContainer.text_compressor
    ],
) -> SimpleTextCompressor:
    """Get text compressor instance."""
    return text_compressor


@inject
def get_ml_client(
    ml_client: TokenAnalysisClient = Provide[ApplicationContainer.ml_client],
) -> TokenAnalysisClient:
    """Get ML client instance."""
    return ml_client


@inject
def get_experiments(
    experiments: TokenLimitExperiments = Provide[ApplicationContainer.experiments],
) -> TokenLimitExperiments:
    """Get experiments instance."""
    return experiments


@inject
def get_token_service(
    token_service: TokenService = Provide[ApplicationContainer.token_service],
) -> TokenService:
    """Get token service instance."""
    return token_service


@inject
def get_token_service_handler(
    handler: TokenServiceHandler = Provide[ApplicationContainer.token_service_handler],
) -> TokenServiceHandler:
    """Get token service handler instance."""
    return handler


@inject
def get_application_context(context=Provide[ApplicationContainer.application_context]):
    """Get application context instance."""
    return context


# Container lifecycle management
def initialize_container(
    config_dict: Optional[Dict[str, Any]] = None,
) -> ApplicationContainer:
    """
    Initialize the container with configuration.

    Args:
        config_dict: Optional configuration dictionary

    Returns:
        ApplicationContainer: Initialized container
    """
    return configure_container(config_dict)


def shutdown_container() -> None:
    """Shutdown the container and cleanup resources."""
    # Cleanup any resources if needed
    unwire_modules()
    # Additional cleanup can be added here


# Container health check
def check_container_health(
    container_instance: Optional[ApplicationContainer] = None,
) -> Dict[str, Any]:
    """
    Check container health and component availability.

    Args:
        container_instance: Optional container instance to check.
                          If None, uses the global container.

    Returns:
        Dict[str, Any]: Health status information
    """
    health_status = {"container_initialized": True, "components": {}}

    # Use provided container or global container
    container_to_check = container_instance or container

    try:
        # Test core components
        health_status["components"]["token_counter"] = (
            container_to_check.token_counter() is not None
        )
        health_status["components"]["text_compressor"] = (
            container_to_check.text_compressor() is not None
        )
        health_status["components"]["ml_client"] = (
            container_to_check.ml_client() is not None
        )
        health_status["components"]["experiments"] = (
            container_to_check.experiments() is not None
        )
        health_status["components"]["token_service"] = (
            container_to_check.token_service() is not None
        )

        # Overall health
        health_status["overall_health"] = all(health_status["components"].values())

    except Exception as e:
        health_status["overall_health"] = False
        health_status["error"] = str(e)

    return health_status
