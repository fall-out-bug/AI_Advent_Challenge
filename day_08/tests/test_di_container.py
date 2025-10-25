"""
Tests for the Dependency Injection Container.

This module contains comprehensive tests for the ApplicationContainer
and related DI functionality.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from core.container import (
    ApplicationContainer,
    configure_container,
    get_container,
    initialize_container,
    shutdown_container,
    check_container_health,
    get_token_counter,
    get_text_compressor,
    get_ml_client,
    get_experiments,
    get_token_service,
    get_token_service_handler,
    get_application_context,
    wire_modules,
    unwire_modules
)
from core.bootstrap.application_bootstrapper import ApplicationBootstrapper, BootstrapError
from core.interfaces.protocols import TokenCounterProtocol
from core.text_compressor import SimpleTextCompressor
from core.ml_client import TokenAnalysisClient
from core.experiments import TokenLimitExperiments
from services.token_service import TokenService
from api.handlers.token_handler import TokenServiceHandler
from models.application_context import ApplicationContext


class TestApplicationContainer:
    """Test cases for ApplicationContainer."""

    def test_container_initialization(self):
        """Test container can be initialized."""
        container = ApplicationContainer()
        assert container is not None
        assert hasattr(container, 'config')
        assert hasattr(container, 'token_counter')
        assert hasattr(container, 'text_compressor')
        assert hasattr(container, 'ml_client')

    def test_container_configuration(self):
        """Test container configuration."""
        config_dict = {
            "ml_service": {
                "url": "http://test:8000"
            },
            "token_counter": {
                "mode": "accurate"
            }
        }
        
        container = configure_container(config_dict)
        assert container.config.ml_service.url() == "http://test:8000"
        assert container.config.token_counter.mode() == "accurate"

    def test_container_default_configuration(self):
        """Test container with default configuration."""
        container = configure_container()
        assert container.config.ml_service.url() == "http://localhost:8004"
        assert container.config.token_counter.mode() == "simple"

    def test_token_counter_provider(self):
        """Test token counter provider."""
        container = configure_container()
        token_counter = container.token_counter()
        
        assert token_counter is not None
        assert hasattr(token_counter, 'count_tokens')
        assert hasattr(token_counter, 'get_model_limits')

    def test_text_compressor_provider(self):
        """Test text compressor provider."""
        container = configure_container()
        text_compressor = container.text_compressor()
        
        assert text_compressor is not None
        assert isinstance(text_compressor, SimpleTextCompressor)

    def test_ml_client_provider(self):
        """Test ML client provider."""
        container = configure_container()
        ml_client = container.ml_client()
        
        assert ml_client is not None
        assert isinstance(ml_client, TokenAnalysisClient)

    def test_experiments_provider(self):
        """Test experiments provider."""
        container = configure_container()
        experiments = container.experiments()
        
        assert experiments is not None
        assert isinstance(experiments, TokenLimitExperiments)

    def test_token_service_provider(self):
        """Test token service provider."""
        container = configure_container()
        token_service = container.token_service()
        
        assert token_service is not None
        assert isinstance(token_service, TokenService)

    def test_token_service_handler_provider(self):
        """Test token service handler provider."""
        container = configure_container()
        handler = container.token_service_handler()
        
        assert handler is not None
        assert isinstance(handler, TokenServiceHandler)

    def test_application_context_provider(self):
        """Test application context provider."""
        container = configure_container()
        context = container.application_context()
        
        assert context is not None
        assert isinstance(context, ApplicationContext)

    def test_singleton_providers(self):
        """Test that singleton providers return same instance."""
        container = configure_container()
        
        ml_client1 = container.ml_client()
        ml_client2 = container.ml_client()
        
        assert ml_client1 is ml_client2  # Should be same instance

    def test_factory_providers(self):
        """Test that factory providers return new instances."""
        container = configure_container()
        
        token_counter1 = container.token_counter()
        token_counter2 = container.token_counter()
        
        assert token_counter1 is not token_counter2  # Should be different instances


class TestContainerFunctions:
    """Test cases for container utility functions."""

    def test_get_container(self):
        """Test get_container function."""
        container = get_container()
        assert container is not None
        # Check that it's a dependency-injector container
        from dependency_injector import containers
        assert isinstance(container, containers.Container)

    def test_initialize_container(self):
        """Test initialize_container function."""
        config = {"ml_service": {"url": "http://test:8000"}}
        container = initialize_container(config)
        
        assert container is not None
        assert container.config.ml_service.url() == "http://test:8000"

    def test_initialize_container_no_config(self):
        """Test initialize_container with no config."""
        container = initialize_container()
        assert container is not None
        assert container.config.ml_service.url() == "http://localhost:8004"

    def test_check_container_health(self):
        """Test container health check."""
        container = configure_container()
        health = check_container_health(container)

        assert health["container_initialized"] is True
        assert health["overall_health"] is True
        assert "components" in health

    def test_check_container_health_unhealthy(self):
        """Test container health check with unhealthy container."""
        # Mock a failing container
        with patch('core.container.container') as mock_container:
            mock_container.token_counter.side_effect = Exception("Test error")
            
            health = check_container_health()
            
            assert health["overall_health"] is False
            assert "error" in health

    def test_shutdown_container(self):
        """Test container shutdown."""
        # This should not raise an exception
        shutdown_container()


class TestInjectionFunctions:
    """Test cases for injection convenience functions."""

    def test_get_token_counter_injection(self):
        """Test get_token_counter injection."""
        container = configure_container()
        
        with patch('core.container.container', container):
            token_counter = get_token_counter()
            assert token_counter is not None

    def test_get_text_compressor_injection(self):
        """Test get_text_compressor injection."""
        container = configure_container()
        
        with patch('core.container.container', container):
            text_compressor = get_text_compressor()
            assert text_compressor is not None

    def test_get_ml_client_injection(self):
        """Test get_ml_client injection."""
        container = configure_container()
        
        with patch('core.container.container', container):
            ml_client = get_ml_client()
            assert ml_client is not None

    def test_get_experiments_injection(self):
        """Test get_experiments injection."""
        container = configure_container()
        
        with patch('core.container.container', container):
            experiments = get_experiments()
            assert experiments is not None

    def test_get_token_service_injection(self):
        """Test get_token_service injection."""
        container = configure_container()
        
        with patch('core.container.container', container):
            token_service = get_token_service()
            assert token_service is not None

    def test_get_token_service_handler_injection(self):
        """Test get_token_service_handler injection."""
        container = configure_container()
        
        with patch('core.container.container', container):
            handler = get_token_service_handler()
            assert handler is not None

    def test_get_application_context_injection(self):
        """Test get_application_context injection."""
        container = configure_container()
        
        with patch('core.container.container', container):
            context = get_application_context()
            assert context is not None


class TestWiringFunctions:
    """Test cases for wiring functions."""

    def test_wire_modules(self):
        """Test wire_modules function."""
        # This should not raise an exception
        wire_modules([])

    def test_unwire_modules(self):
        """Test unwire_modules function."""
        # This should not raise an exception
        unwire_modules()


class TestApplicationBootstrapperWithContainer:
    """Test cases for ApplicationBootstrapper with DI container."""

    def test_bootstrapper_initialization(self):
        """Test bootstrapper initialization."""
        config = {"ml_service": {"url": "http://test:8000"}}
        bootstrapper = ApplicationBootstrapper(config)
        
        assert bootstrapper.config == config
        assert bootstrapper.container is None

    def test_bootstrap_with_container(self):
        """Test bootstrap using DI container."""
        config = {"ml_service": {"url": "http://test:8000"}}
        bootstrapper = ApplicationBootstrapper(config)
        
        context = bootstrapper.bootstrap()
        
        assert context is not None
        assert isinstance(context, ApplicationContext)
        assert bootstrapper.container is not None

    def test_bootstrap_info(self):
        """Test bootstrap info."""
        config = {"test_key": "test_value"}
        bootstrapper = ApplicationBootstrapper(config)
        
        info = bootstrapper.get_bootstrap_info()
        
        assert info["config_keys"] == ["test_key"]
        assert info["config_available"] is True
        assert info["logger_configured"] is True
        assert info["container_initialized"] is False

    def test_bootstrap_info_after_bootstrap(self):
        """Test bootstrap info after bootstrap."""
        bootstrapper = ApplicationBootstrapper()
        bootstrapper.bootstrap()
        
        info = bootstrapper.get_bootstrap_info()
        
        assert info["container_initialized"] is True
        assert info["container_health"] is not None

    def test_get_container(self):
        """Test get_container method."""
        bootstrapper = ApplicationBootstrapper()
        assert bootstrapper.get_container() is None
        
        bootstrapper.bootstrap()
        container = bootstrapper.get_container()
        
        assert container is not None
        # Check that it's a dependency-injector container
        from dependency_injector import containers
        assert isinstance(container, containers.Container)

    def test_container_health_check(self):
        """Test container health check."""
        bootstrapper = ApplicationBootstrapper()
        bootstrapper.bootstrap()
        
        health = bootstrapper._check_container_health()
        
        assert health["status"] == "healthy"
        assert "components" in health

    def test_container_health_check_unhealthy(self):
        """Test container health check with unhealthy container."""
        bootstrapper = ApplicationBootstrapper()
        bootstrapper.bootstrap()
        
        # Mock container to raise exception
        with patch.object(bootstrapper.container, 'token_counter', side_effect=Exception("Test error")):
            health = bootstrapper._check_container_health()
            
            assert health["status"] == "unhealthy"
            assert "error" in health

    def test_bootstrap_error_handling(self):
        """Test bootstrap error handling."""
        bootstrapper = ApplicationBootstrapper()
        
        # Mock configure_container to raise exception
        with patch('core.bootstrap.application_bootstrapper.configure_container', side_effect=Exception("Container error")):
            with pytest.raises(BootstrapError) as exc_info:
                bootstrapper.bootstrap()
            
            assert "Failed to bootstrap application" in str(exc_info.value)


class TestContainerIntegration:
    """Integration tests for container functionality."""

    def test_full_bootstrap_workflow(self):
        """Test complete bootstrap workflow."""
        config = {
            "ml_service": {"url": "http://test:8000"},
            "token_counter": {"mode": "accurate"}
        }
        
        bootstrapper = ApplicationBootstrapper(config)
        context = bootstrapper.bootstrap()
        
        # Verify all components are properly initialized
        assert context.token_counter is not None
        assert context.text_compressor is not None
        assert context.ml_client is not None
        assert context.experiments is not None
        assert context.reporter is not None
        assert context.logger is not None
        
        # Verify context validation passes
        assert context.validate_components() is True

    def test_container_component_dependencies(self):
        """Test that container properly resolves component dependencies."""
        container = configure_container()
        
        # Get components and verify they have proper dependencies
        token_counter = container.token_counter()
        text_compressor = container.text_compressor()
        experiments = container.experiments()
        
        # Text compressor should have token_counter dependency
        assert isinstance(text_compressor.token_counter, type(token_counter))
        
        # Experiments should have all dependencies
        assert experiments.model_client is not None
        assert isinstance(experiments.token_counter, type(token_counter))
        assert isinstance(experiments.text_compressor, type(text_compressor))

    def test_multiple_container_instances(self):
        """Test that multiple container instances work independently."""
        config1 = {"ml_service": {"url": "http://test1:8000"}}
        config2 = {"ml_service": {"url": "http://test2:8000"}}
        
        container1 = configure_container(config1)
        container2 = configure_container(config2)
        
        assert container1.config.ml_service.url() == "http://test1:8000"
        assert container2.config.ml_service.url() == "http://test2:8000"
        
        # Should be different instances
        assert container1 is not container2
