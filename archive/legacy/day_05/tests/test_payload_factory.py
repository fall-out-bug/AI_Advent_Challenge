"""
Tests for API payload factory.
"""

import pytest

from utils.payload_factory import PayloadFactory, PayloadConfig


class TestPayloadFactory:
    """Test PayloadFactory functionality."""
    
    def test_create_perplexity_payload_basic(self):
        """Test basic Perplexity payload creation."""
        config = PayloadConfig(model="sonar-pro", max_tokens=800, temperature=0.7)
        payload = PayloadFactory.create_perplexity_payload("Hello", config)
        
        assert payload["model"] == "sonar-pro"
        assert payload["max_tokens"] == 800
        assert payload["temperature"] == 0.7
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "Hello"
    
    def test_create_perplexity_payload_with_system(self):
        """Test Perplexity payload with system prompt."""
        config = PayloadConfig(
            model="sonar-pro", 
            max_tokens=500, 
            temperature=0.5,
            system_prompt="You are helpful"
        )
        payload = PayloadFactory.create_perplexity_payload("Hello", config)
        
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "You are helpful"
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == "Hello"
    
    def test_create_chadgpt_payload_basic(self):
        """Test basic ChadGPT payload creation."""
        config = PayloadConfig(model="gpt-5-mini", max_tokens=600, temperature=0.8)
        payload = PayloadFactory.create_chadgpt_payload("Hello", config, "test_key")
        
        assert payload["message"] == "Hello"
        assert payload["api_key"] == "test_key"
        assert payload["temperature"] == 0.8
        assert payload["max_tokens"] == 600
    
    def test_create_chadgpt_payload_with_system(self):
        """Test ChadGPT payload with system prompt."""
        config = PayloadConfig(
            model="gpt-5-mini", 
            max_tokens=400, 
            temperature=0.6,
            system_prompt="You are helpful"
        )
        payload = PayloadFactory.create_chadgpt_payload("Hello", config, "test_key")
        
        expected_message = "You are helpful\n\nВопрос: Hello"
        assert payload["message"] == expected_message
    
    def test_create_local_payload(self):
        """Test local model payload creation."""
        config = PayloadConfig(model="qwen", max_tokens=1000, temperature=0.9)
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        payload = PayloadFactory.create_local_payload(messages, config)
        
        assert payload["messages"] == messages
        assert payload["max_tokens"] == 1000
        assert payload["temperature"] == 0.9
    
    def test_create_availability_check_payload(self):
        """Test availability check payload creation."""
        payload = PayloadFactory.create_availability_check_payload()
        
        assert payload["messages"][0]["role"] == "user"
        assert payload["messages"][0]["content"] == "test"
        assert payload["max_tokens"] == 1
    
    def test_create_chat_messages_basic(self):
        """Test basic chat messages creation."""
        messages = PayloadFactory.create_chat_messages("Hello")
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
    
    def test_create_chat_messages_with_system(self):
        """Test chat messages creation with system prompt."""
        messages = PayloadFactory.create_chat_messages("Hello", "You are helpful")
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are helpful"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"


class TestPayloadConfig:
    """Test PayloadConfig dataclass."""
    
    def test_payload_config_defaults(self):
        """Test PayloadConfig with default values."""
        config = PayloadConfig(model="test-model")
        
        assert config.model == "test-model"
        assert config.max_tokens == 800
        assert config.temperature == 0.7
        assert config.system_prompt is None
    
    def test_payload_config_custom(self):
        """Test PayloadConfig with custom values."""
        config = PayloadConfig(
            model="test-model",
            max_tokens=500,
            temperature=0.5,
            system_prompt="Custom prompt"
        )
        
        assert config.model == "test-model"
        assert config.max_tokens == 500
        assert config.temperature == 0.5
        assert config.system_prompt == "Custom prompt"
