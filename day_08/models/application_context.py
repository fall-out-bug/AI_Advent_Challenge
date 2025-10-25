"""
Application context for runtime state management.

This module defines the ApplicationContext dataclass that holds
all application components and configuration for runtime execution.
"""

from dataclasses import dataclass
from typing import Optional

from core.experiments import TokenLimitExperiments
from core.interfaces.protocols import TokenCounterProtocol
from core.ml_client import TokenAnalysisClient
from core.text_compressor import SimpleTextCompressor
from utils.console_reporter import ConsoleReporter
from utils.logging import LoggerFactory


@dataclass
class ApplicationContext:
    """
    Application runtime context.
    
    Holds all application components and configuration needed
    for runtime execution. This provides a clean way to pass
    dependencies between different parts of the application.
    
    Attributes:
        token_counter: Token counting service
        text_compressor: Text compression service
        ml_client: ML service client for external API calls
        experiments: Experiment orchestration service
        reporter: Console reporting service
        logger: Application logger
        config: Application configuration (optional)
    """
    
    token_counter: TokenCounterProtocol
    text_compressor: SimpleTextCompressor
    ml_client: TokenAnalysisClient
    experiments: TokenLimitExperiments
    reporter: ConsoleReporter
    logger: LoggerFactory
    
    # Optional configuration
    config: Optional[dict] = None
    
    def __post_init__(self):
        """Initialize logger after dataclass creation."""
        if not hasattr(self, 'logger') or self.logger is None:
            self.logger = LoggerFactory.create_logger(__name__)
    
    def get_component_status(self) -> dict:
        """
        Get status of all components.
        
        Returns:
            dict: Status information for all components
        """
        return {
            'token_counter': type(self.token_counter).__name__,
            'text_compressor': type(self.text_compressor).__name__,
            'ml_client': type(self.ml_client).__name__,
            'experiments': type(self.experiments).__name__,
            'reporter': type(self.reporter).__name__,
            'logger': type(self.logger).__name__,
            'config_available': self.config is not None
        }
    
    def validate_components(self) -> bool:
        """
        Validate that all required components are properly initialized.
        
        Returns:
            bool: True if all components are valid, False otherwise
        """
        required_components = [
            self.token_counter,
            self.text_compressor,
            self.ml_client,
            self.experiments,
            self.reporter,
            self.logger
        ]
        
        return all(component is not None for component in required_components)
    
    async def cleanup(self) -> None:
        """
        Clean up resources used by components.
        
        This method should be called when the application context
        is no longer needed to properly release resources.
        """
        try:
            # Close async clients if they have cleanup methods
            if hasattr(self.ml_client, 'close'):
                await self.ml_client.close()
            
            if hasattr(self.token_counter, 'close'):
                await self.token_counter.close()
            
            self.logger.info("Application context cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_summary(self) -> str:
        """
        Get a summary of the application context.
        
        Returns:
            str: Human-readable summary of the context
        """
        status = self.get_component_status()
        return f"""
Application Context Summary:
- Token Counter: {status['token_counter']}
- Text Compressor: {status['text_compressor']}
- ML Client: {status['ml_client']}
- Experiments: {status['experiments']}
- Reporter: {status['reporter']}
- Logger: {status['logger']}
- Config Available: {status['config_available']}
- Components Valid: {self.validate_components()}
        """.strip()
