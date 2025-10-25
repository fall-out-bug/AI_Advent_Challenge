"""
Builder pattern for ExperimentResult construction.

Provides a fluent interface for building ExperimentResult
objects with proper validation and defaults.
"""

from typing import Optional
from datetime import datetime
from models.data_models import ExperimentResult, CompressionResult


class ExperimentResultBuilder:
    """
    Builder pattern for ExperimentResult.
    
    Provides a fluent interface for constructing ExperimentResult
    objects with proper validation and defaults.
    """
    
    def __init__(self):
        """Initialize builder with empty result."""
        self._result = {}
    
    def with_experiment_name(self, name: str) -> 'ExperimentResultBuilder':
        """
        Set experiment name.
        
        Args:
            name: Name of the experiment
            
        Returns:
            Self for method chaining
        """
        self._result['experiment_name'] = name
        return self
    
    def with_model(self, model_name: str) -> 'ExperimentResultBuilder':
        """
        Set model name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Self for method chaining
        """
        self._result['model_name'] = model_name
        return self
    
    def with_query(self, original: str, processed: str) -> 'ExperimentResultBuilder':
        """
        Set query information.
        
        Args:
            original: Original query text
            processed: Processed query text
            
        Returns:
            Self for method chaining
        """
        self._result['original_query'] = original
        self._result['processed_query'] = processed
        return self
    
    def with_response(self, response: str) -> 'ExperimentResultBuilder':
        """
        Set response text.
        
        Args:
            response: Response text from model
            
        Returns:
            Self for method chaining
        """
        self._result['response'] = response
        return self
    
    def with_tokens(self, input_t: int, output_t: int, total: int) -> 'ExperimentResultBuilder':
        """
        Set token counts.
        
        Args:
            input_t: Input token count
            output_t: Output token count
            total: Total token count
            
        Returns:
            Self for method chaining
        """
        self._result['input_tokens'] = input_t
        self._result['output_tokens'] = output_t
        self._result['total_tokens'] = total
        return self
    
    def with_timing(self, duration: float) -> 'ExperimentResultBuilder':
        """
        Set response timing.
        
        Args:
            duration: Response duration in seconds
            
        Returns:
            Self for method chaining
        """
        self._result['response_time'] = duration
        return self
    
    def with_compression(
        self, 
        applied: bool, 
        result: Optional[CompressionResult] = None
    ) -> 'ExperimentResultBuilder':
        """
        Set compression information.
        
        Args:
            applied: Whether compression was applied
            result: Compression result if applied
            
        Returns:
            Self for method chaining
        """
        self._result['compression_applied'] = applied
        self._result['compression_result'] = result
        return self
    
    def with_timestamp(self, timestamp: Optional[datetime] = None) -> 'ExperimentResultBuilder':
        """
        Set experiment timestamp.
        
        Args:
            timestamp: Timestamp (defaults to now)
            
        Returns:
            Self for method chaining
        """
        self._result['timestamp'] = timestamp or datetime.now()
        return self
    
    def build(self) -> ExperimentResult:
        """
        Build ExperimentResult from collected data.
        
        Returns:
            ExperimentResult: Constructed experiment result
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            'experiment_name', 'model_name', 'original_query', 
            'processed_query', 'response', 'input_tokens', 
            'output_tokens', 'total_tokens', 'response_time'
        ]
        
        missing_fields = [field for field in required_fields if field not in self._result]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Set defaults for optional fields
        self._result.setdefault('compression_applied', False)
        self._result.setdefault('compression_result', None)
        self._result.setdefault('timestamp', datetime.now())
        
        return ExperimentResult(**self._result)
