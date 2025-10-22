"""
Builder pattern for ModelResponse objects.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import sys
import os

# Add shared SDK to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'shared'))

from shared_package.clients.base_client import ModelResponse


class ModelResponseBuilder:
    """Builder for ModelResponse objects."""
    
    def __init__(self):
        """Initialize builder with default values."""
        self._response = ""
        self._response_tokens = 0
        self._input_tokens = 0
        self._total_tokens = 0
        self._model_name = ""
        self._response_time = 0.0
    
    def response(self, text: str) -> 'ModelResponseBuilder':
        """Set response text."""
        self._response = text
        return self
    
    def response_tokens(self, count: int) -> 'ModelResponseBuilder':
        """Set response token count."""
        self._response_tokens = count
        return self
    
    def input_tokens(self, count: int) -> 'ModelResponseBuilder':
        """Set input token count."""
        self._input_tokens = count
        return self
    
    def total_tokens(self, count: int) -> 'ModelResponseBuilder':
        """Set total token count."""
        self._total_tokens = count
        return self
    
    def model_name(self, name: str) -> 'ModelResponseBuilder':
        """Set model name."""
        self._model_name = name
        return self
    
    def response_time(self, time: float) -> 'ModelResponseBuilder':
        """Set response time."""
        self._response_time = time
        return self
    
    def auto_calculate_total_tokens(self) -> 'ModelResponseBuilder':
        """Automatically calculate total tokens."""
        self._total_tokens = self._input_tokens + self._response_tokens
        return self
    
    def estimate_tokens(self, prompt: str, response: str) -> 'ModelResponseBuilder':
        """Estimate token counts for external APIs."""
        self._input_tokens = int(len(prompt.split()) * 1.3)
        self._response_tokens = int(len(response.split()) * 1.3)
        self._total_tokens = self._input_tokens + self._response_tokens
        return self
    
    def build(self) -> ModelResponse:
        """Build ModelResponse object."""
        return ModelResponse(
            response=self._response,
            response_tokens=self._response_tokens,
            input_tokens=self._input_tokens,
            total_tokens=self._total_tokens,
            model_name=self._model_name,
            response_time=self._response_time
        )
    
    def reset(self) -> 'ModelResponseBuilder':
        """Reset builder to initial state."""
        self._response = ""
        self._response_tokens = 0
        self._input_tokens = 0
        self._total_tokens = 0
        self._model_name = ""
        self._response_time = 0.0
        return self


class ModelResponseFactory:
    """Factory for creating common ModelResponse patterns."""
    
    @staticmethod
    def create_local_response(
        response_text: str,
        input_tokens: int,
        response_tokens: int,
        model_name: str,
        response_time: float
    ) -> ModelResponse:
        """Create response for local model."""
        return (ModelResponseBuilder()
                .response(response_text)
                .input_tokens(input_tokens)
                .response_tokens(response_tokens)
                .model_name(model_name)
                .response_time(response_time)
                .auto_calculate_total_tokens()
                .build())
    
    @staticmethod
    def create_external_response(
        response_text: str,
        prompt: str,
        model_name: str,
        response_time: float
    ) -> ModelResponse:
        """Create response for external API with token estimation."""
        return (ModelResponseBuilder()
                .response(response_text)
                .model_name(model_name)
                .response_time(response_time)
                .estimate_tokens(prompt, response_text)
                .build())
    
    @staticmethod
    def create_error_response(
        error_message: str,
        model_name: str
    ) -> ModelResponse:
        """Create error response."""
        return (ModelResponseBuilder()
                .response(error_message)
                .model_name(model_name)
                .response_time(0.0)
                .build())
    
    @staticmethod
    def create_test_response(
        response_text: str = "Test response",
        model_name: str = "test-model"
    ) -> ModelResponse:
        """Create test response."""
        return (ModelResponseBuilder()
                .response(response_text)
                .input_tokens(5)
                .response_tokens(10)
                .model_name(model_name)
                .response_time(0.1)
                .auto_calculate_total_tokens()
                .build())
