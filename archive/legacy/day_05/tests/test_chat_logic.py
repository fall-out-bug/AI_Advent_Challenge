"""
Tests for business/chat_logic.py module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from business.chat_logic import ChatLogic
from state.chat_state import ChatState


class TestChatLogic:
    """Test ChatLogic functionality."""
    
    @pytest.fixture
    def mock_state(self):
        """Create mock chat state."""
        state = MagicMock(spec=ChatState)
        state.current_api = "perplexity"
        state.api_key = "test-api-key"
        state.client = AsyncMock()
        state.get_system_prompt.return_value = "Test system prompt"
        state.local_clients = {}
        return state
    
    @pytest.fixture
    def chat_logic(self, mock_state):
        """Create ChatLogic instance."""
        return ChatLogic(mock_state)
    
    def test_init(self, mock_state):
        """Test ChatLogic initialization."""
        logic = ChatLogic(mock_state)
        
        assert logic.state == mock_state
        assert "perplexity" in logic.api_config
        assert "chadgpt" in logic.api_config
        assert logic.api_config["perplexity"]["model"] == "sonar-pro"
    
    @pytest.mark.asyncio
    async def test_call_model_perplexity(self, chat_logic, mock_state):
        """Test calling Perplexity API."""
        mock_state.current_api = "perplexity"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_state.client.post.return_value = mock_response
        
        result = await chat_logic.call_model("test message", 0.7)
        
        assert result["response"] == "Test response"
        assert result["input_tokens"] == 0
        assert result["response_tokens"] == 0
        assert result["total_tokens"] == 0
    
    @pytest.mark.asyncio
    async def test_call_model_chadgpt(self, chat_logic, mock_state):
        """Test calling ChadGPT API."""
        mock_state.current_api = "chadgpt"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "is_success": True,
            "response": "ChadGPT response"
        }
        mock_state.client.post.return_value = mock_response
        
        result = await chat_logic.call_model("test message", 0.7)
        
        assert result["response"] == "ChadGPT response"
    
    def test_parse_temp_override_valid(self, chat_logic):
        """Test parsing valid temperature override."""
        temp, message = chat_logic.parse_temp_override("temp=0.8 Hello world")
        
        assert temp == 0.8
        assert message == "Hello world"
    
    def test_parse_temp_override_invalid(self, chat_logic):
        """Test parsing invalid temperature override."""
        temp, message = chat_logic.parse_temp_override("temp=invalid Hello world")
        
        assert temp is None
        assert message == "Hello world"
    
    def test_parse_temp_override_no_temp(self, chat_logic):
        """Test parsing message without temperature override."""
        temp, message = chat_logic.parse_temp_override("Hello world")
        
        assert temp is None
        assert message == "Hello world"
    
    def test_apply_interactive_temperature_calm(self, chat_logic, mock_state):
        """Test applying calm temperature."""
        chat_logic.apply_interactive_temperature("не душни, пожалуйста")
        
        mock_state.set_temperature.assert_called_with(0.0)
    
    def test_apply_interactive_temperature_normal(self, chat_logic, mock_state):
        """Test applying normal temperature."""
        chat_logic.apply_interactive_temperature("потише, не так быстро")
        
        mock_state.set_temperature.assert_called_with(0.7)
    
    def test_apply_interactive_temperature_aggressive(self, chat_logic, mock_state):
        """Test applying aggressive temperature."""
        chat_logic.apply_interactive_temperature("разгоняй, давай быстрее")
        
        mock_state.set_temperature.assert_called_with(1.2)
    
    def test_switch_model_local(self, chat_logic, mock_state):
        """Test switching to local model."""
        result = chat_logic.switch_model("local-qwen")
        
        assert result is True
        assert mock_state.current_api == "qwen"
    
    def test_switch_model_external(self, chat_logic, mock_state):
        """Test switching to external model."""
        result = chat_logic.switch_model("chadgpt")
        
        assert result is True
        assert mock_state.current_api == "chadgpt"
    
    def test_switch_model_invalid(self, chat_logic, mock_state):
        """Test switching to invalid model."""
        result = chat_logic.switch_model("invalid-model")
        
        assert result is False
        # current_api should not change
        assert mock_state.current_api == "perplexity"
