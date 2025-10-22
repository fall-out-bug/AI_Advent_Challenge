"""
Tests for ModelResponse builder pattern.
"""

import pytest

from utils.response_builder import ModelResponseBuilder, ModelResponseFactory
from shared_package.clients.base_client import ModelResponse


class TestModelResponseBuilder:
    """Test ModelResponseBuilder functionality."""
    
    def test_builder_initialization(self):
        """Test builder initialization."""
        builder = ModelResponseBuilder()
        
        assert builder._response == ""
        assert builder._response_tokens == 0
        assert builder._input_tokens == 0
        assert builder._total_tokens == 0
        assert builder._model_name == ""
        assert builder._response_time == 0.0
    
    def test_builder_fluent_interface(self):
        """Test builder fluent interface."""
        builder = ModelResponseBuilder()
        
        # Test method chaining
        result = (builder
                 .response("Test response")
                 .response_tokens(10)
                 .input_tokens(5)
                 .model_name("test-model")
                 .response_time(0.1))
        
        assert result is builder  # Should return self
    
    def test_build_basic_response(self):
        """Test building basic response."""
        response = (ModelResponseBuilder()
                   .response("Hello world")
                   .response_tokens(2)
                   .input_tokens(1)
                   .total_tokens(3)
                   .model_name("qwen")
                   .response_time(0.5)
                   .build())
        
        assert isinstance(response, ModelResponse)
        assert response.response == "Hello world"
        assert response.response_tokens == 2
        assert response.input_tokens == 1
        assert response.total_tokens == 3
        assert response.model_name == "qwen"
        assert response.response_time == 0.5
    
    def test_auto_calculate_total_tokens(self):
        """Test automatic total tokens calculation."""
        response = (ModelResponseBuilder()
                   .response("Test")
                   .input_tokens(5)
                   .response_tokens(10)
                   .model_name("test")
                   .auto_calculate_total_tokens()
                   .build())
        
        assert response.total_tokens == 15  # 5 + 10
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        prompt = "Hello world"
        response_text = "Hi there"
        
        response = (ModelResponseBuilder()
                   .response(response_text)
                   .model_name("test")
                   .estimate_tokens(prompt, response_text)
                   .build())
        
        # Should estimate tokens based on word count * 1.3
        expected_input = int(len(prompt.split()) * 1.3)  # 2 * 1.3 = 2
        expected_response = int(len(response_text.split()) * 1.3)  # 2 * 1.3 = 2
        
        assert response.input_tokens == expected_input
        assert response.response_tokens == expected_response
        assert response.total_tokens == expected_input + expected_response
    
    def test_reset(self):
        """Test builder reset."""
        builder = (ModelResponseBuilder()
                  .response("Test")
                  .response_tokens(5)
                  .input_tokens(3)
                  .model_name("test")
                  .response_time(0.2))
        
        # Reset and verify
        builder.reset()
        
        assert builder._response == ""
        assert builder._response_tokens == 0
        assert builder._input_tokens == 0
        assert builder._total_tokens == 0
        assert builder._model_name == ""
        assert builder._response_time == 0.0


class TestModelResponseFactory:
    """Test ModelResponseFactory functionality."""
    
    def test_create_local_response(self):
        """Test creating local model response."""
        response = ModelResponseFactory.create_local_response(
            response_text="Local response",
            input_tokens=5,
            response_tokens=10,
            model_name="qwen",
            response_time=0.3
        )
        
        assert isinstance(response, ModelResponse)
        assert response.response == "Local response"
        assert response.input_tokens == 5
        assert response.response_tokens == 10
        assert response.total_tokens == 15  # Auto-calculated
        assert response.model_name == "qwen"
        assert response.response_time == 0.3
    
    def test_create_external_response(self):
        """Test creating external API response."""
        prompt = "Hello"
        response_text = "Hi there"
        
        response = ModelResponseFactory.create_external_response(
            response_text=response_text,
            prompt=prompt,
            model_name="perplexity",
            response_time=0.5
        )
        
        assert isinstance(response, ModelResponse)
        assert response.response == response_text
        assert response.model_name == "perplexity"
        assert response.response_time == 0.5
        
        # Should have estimated tokens
        expected_input = int(len(prompt.split()) * 1.3)
        expected_response = int(len(response_text.split()) * 1.3)
        
        assert response.input_tokens == expected_input
        assert response.response_tokens == expected_response
        assert response.total_tokens == expected_input + expected_response
    
    def test_create_error_response(self):
        """Test creating error response."""
        response = ModelResponseFactory.create_error_response(
            error_message="❌ Connection failed",
            model_name="unknown"
        )
        
        assert isinstance(response, ModelResponse)
        assert response.response == "❌ Connection failed"
        assert response.model_name == "unknown"
        assert response.response_time == 0.0
        assert response.input_tokens == 0
        assert response.response_tokens == 0
        assert response.total_tokens == 0
    
    def test_create_test_response_defaults(self):
        """Test creating test response with defaults."""
        response = ModelResponseFactory.create_test_response()
        
        assert isinstance(response, ModelResponse)
        assert response.response == "Test response"
        assert response.model_name == "test-model"
        assert response.input_tokens == 5
        assert response.response_tokens == 10
        assert response.total_tokens == 15
        assert response.response_time == 0.1
    
    def test_create_test_response_custom(self):
        """Test creating test response with custom values."""
        response = ModelResponseFactory.create_test_response(
            response_text="Custom test",
            model_name="custom-model"
        )
        
        assert isinstance(response, ModelResponse)
        assert response.response == "Custom test"
        assert response.model_name == "custom-model"
        assert response.input_tokens == 5
        assert response.response_tokens == 10
        assert response.total_tokens == 15
        assert response.response_time == 0.1


class TestBuilderPatternIntegration:
    """Test builder pattern integration scenarios."""
    
    def test_complex_response_building(self):
        """Test building complex response with multiple steps."""
        response = (ModelResponseBuilder()
                   .response("This is a complex response with multiple words")
                   .model_name("mistral")
                   .response_time(1.5)
                   .estimate_tokens("Complex prompt", "This is a complex response with multiple words")
                   .build())
        
        assert isinstance(response, ModelResponse)
        assert response.response == "This is a complex response with multiple words"
        assert response.model_name == "mistral"
        assert response.response_time == 1.5
        assert response.input_tokens > 0
        assert response.response_tokens > 0
        assert response.total_tokens == response.input_tokens + response.response_tokens
    
    def test_builder_reuse(self):
        """Test reusing builder instance."""
        builder = ModelResponseBuilder()
        
        # Build first response
        response1 = (builder
                    .response("First response")
                    .model_name("model1")
                    .response_tokens(5)
                    .input_tokens(3)
                    .auto_calculate_total_tokens()
                    .build())
        
        # Reset and build second response
        response2 = (builder
                    .reset()
                    .response("Second response")
                    .model_name("model2")
                    .response_tokens(8)
                    .input_tokens(4)
                    .auto_calculate_total_tokens()
                    .build())
        
        assert response1.response == "First response"
        assert response1.model_name == "model1"
        assert response1.total_tokens == 8
        
        assert response2.response == "Second response"
        assert response2.model_name == "model2"
        assert response2.total_tokens == 12
