"""
Tests for state/chat_state.py module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from state.chat_state import ChatState


class TestChatState:
    """Test ChatState functionality."""
    
    @pytest.fixture
    def chat_state(self):
        """Create ChatState instance."""
        return ChatState()
    
    def test_init(self, chat_state):
        """Test ChatState initialization."""
        assert chat_state.api_key is None
        assert chat_state.client is None
        assert chat_state.default_temperature == 0.5
        assert chat_state.explain_mode is False
        assert chat_state.current_api is None
        assert chat_state.advice_mode is None
        assert chat_state.use_history is False
        assert "Ты пожилой человек" in chat_state._system_prompt
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, chat_state):
        """Test async context manager."""
        async with chat_state as state:
            assert state.client is not None
            assert state.client.timeout == 30.0
        
        # Client should be closed after context
        assert chat_state.client is None
    
    @patch('state.chat_state.is_api_key_configured')
    @patch('state.chat_state.get_api_key')
    def test_setup_external_api_chadgpt(self, mock_get_key, mock_is_configured, chat_state):
        """Test setup with ChadGPT API."""
        mock_is_configured.side_effect = lambda api: api == "chadgpt"
        mock_get_key.return_value = "test-chadgpt-key"
        
        result = chat_state.setup()
        
        assert result is True
        assert chat_state.current_api == "chadgpt"
        assert chat_state.api_key == "test-chadgpt-key"
    
    @patch('state.chat_state.is_api_key_configured')
    @patch('state.chat_state.get_api_key')
    def test_setup_external_api_perplexity(self, mock_get_key, mock_is_configured, chat_state):
        """Test setup with Perplexity API."""
        mock_is_configured.side_effect = lambda api: api == "perplexity"
        mock_get_key.return_value = "test-perplexity-key"
        
        result = chat_state.setup()
        
        assert result is True
        assert chat_state.current_api == "perplexity"
        assert chat_state.api_key == "test-perplexity-key"
    
    def test_setup_local_models(self, chat_state):
        """Test setup with local models."""
        # Mock local clients to be available
        chat_state.local_clients = {"mistral": MagicMock(), "qwen": MagicMock()}
        
        result = chat_state.setup()
        
        assert result is True
        assert chat_state.current_api == "mistral"
    
    @patch('state.chat_state.is_api_key_configured')
    def test_setup_no_apis(self, mock_is_configured, chat_state):
        """Test setup with no available APIs."""
        mock_is_configured.return_value = False
        chat_state.local_clients = {}  # No local models
        
        result = chat_state.setup()
        
        assert result is False
        assert chat_state.current_api is None
    
    def test_set_temperature(self, chat_state):
        """Test setting temperature."""
        chat_state.set_temperature(0.8)
        
        assert chat_state.default_temperature == 0.8
    
    def test_toggle_explain_mode(self, chat_state):
        """Test toggling explain mode."""
        assert chat_state.explain_mode is False
        
        chat_state.toggle_explain_mode()
        assert chat_state.explain_mode is True
        
        chat_state.toggle_explain_mode()
        assert chat_state.explain_mode is False
    
    def test_set_explain_mode(self, chat_state):
        """Test setting explain mode."""
        chat_state.set_explain_mode(True)
        assert chat_state.explain_mode is True
        
        chat_state.set_explain_mode(False)
        assert chat_state.explain_mode is False
    
    def test_switch_model_local(self, chat_state):
        """Test switching to local model."""
        result = chat_state.switch_model("qwen")
        
        assert result is True
        assert chat_state.current_api == "qwen"
    
    def test_switch_model_invalid(self, chat_state):
        """Test switching to invalid model."""
        result = chat_state.switch_model("invalid-model")
        
        assert result is False
        assert chat_state.current_api is None
    
    def test_get_current_model(self, chat_state):
        """Test getting current model."""
        chat_state.current_api = "perplexity"
        
        model = chat_state.get_current_model()
        
        assert model == "perplexity"
    
    def test_get_current_model_none(self, chat_state):
        """Test getting current model when none set."""
        model = chat_state.get_current_model()
        
        assert model == "unknown"
    
    def test_get_system_prompt(self, chat_state):
        """Test getting system prompt."""
        prompt = chat_state.get_system_prompt()
        
        assert "Ты пожилой человек" in prompt
    
    def test_set_system_prompt(self, chat_state):
        """Test setting system prompt."""
        new_prompt = "New system prompt"
        chat_state.set_system_prompt(new_prompt)
        
        assert chat_state._system_prompt == new_prompt
    
    def test_toggle_history(self, chat_state):
        """Test toggling history usage."""
        assert chat_state.use_history is False
        
        chat_state.toggle_history()
        assert chat_state.use_history is True
        
        chat_state.toggle_history()
        assert chat_state.use_history is False
    
    def test_set_history_usage(self, chat_state):
        """Test setting history usage."""
        chat_state.set_history_usage(True)
        assert chat_state.use_history is True
        
        chat_state.set_history_usage(False)
        assert chat_state.use_history is False
