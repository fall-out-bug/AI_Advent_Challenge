"""
Tests for terminal_chat_v5_zen.py module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from terminal_chat_v5_zen import DedChatV5Zen


class TestDedChatV5Zen:
    """Test DedChatV5Zen functionality."""
    
    @pytest.fixture
    def chat_app(self):
        """Create DedChatV5Zen instance."""
        return DedChatV5Zen()
    
    def test_init(self, chat_app):
        """Test DedChatV5Zen initialization."""
        assert chat_app.state is not None
        assert chat_app.ui is not None
        assert chat_app.logic is not None
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, chat_app):
        """Test async context manager."""
        async with chat_app as app:
            assert app.state.client is not None
        
        # Client should be closed after context
        assert chat_app.state.client is None
    
    def test_setup_success(self, chat_app):
        """Test successful setup."""
        chat_app.state.setup.return_value = True
        
        result = chat_app.setup()
        
        assert result is True
        chat_app.state.setup.assert_called_once()
    
    def test_setup_failure(self, chat_app):
        """Test failed setup."""
        chat_app.state.setup.return_value = False
        
        result = chat_app.setup()
        
        assert result is False
    
    def test_handle_command_exit(self, chat_app):
        """Test handling exit command."""
        with patch('sys.exit') as mock_exit:
            result = chat_app._handle_command("покеда")
            
            assert result is True
            mock_exit.assert_called_once_with(0)
    
    def test_handle_command_explain_mode_on(self, chat_app):
        """Test handling explain mode on command."""
        result = chat_app._handle_command("объясняй")
        
        assert result is True
        chat_app.state.set_explain_mode.assert_called_once_with(True)
        chat_app.ui.print_success.assert_called_once_with("Режим пояснений включен")
    
    def test_handle_command_explain_mode_off(self, chat_app):
        """Test handling explain mode off command."""
        chat_app.state.advice_mode = MagicMock()
        
        result = chat_app._handle_command("надоел")
        
        assert result is True
        chat_app.state.set_explain_mode.assert_called_once_with(False)
        assert chat_app.state.advice_mode is None
    
    def test_handle_command_advice_mode(self, chat_app):
        """Test handling advice mode command."""
        with patch('advice_mode_v5.AdviceModeV5') as mock_advice:
            result = chat_app._handle_command("дай совет")
            
            assert result is True
            mock_advice.assert_called_once()
            chat_app.ui.print_success.assert_called_once_with("Режим советчика включен")
    
    def test_handle_command_temp_valid(self, chat_app):
        """Test handling valid temperature command."""
        result = chat_app._handle_command("temp 0.8")
        
        assert result is True
        chat_app.state.set_temperature.assert_called_once_with(0.8)
        chat_app.ui.print_success.assert_called_once_with("Температура установлена: 0.80")
    
    def test_handle_command_temp_invalid(self, chat_app):
        """Test handling invalid temperature command."""
        result = chat_app._handle_command("temp invalid")
        
        assert result is True
        chat_app.ui.print_error.assert_called_once_with("Неверный формат: temp <value>")
    
    def test_handle_command_api_valid(self, chat_app):
        """Test handling valid API command."""
        chat_app.logic.switch_model.return_value = True
        
        result = chat_app._handle_command("api chadgpt")
        
        assert result is True
        chat_app.logic.switch_model.assert_called_once_with("chadgpt")
        chat_app.ui.print_success.assert_called_once_with("Переключено на: chadgpt")
    
    def test_handle_command_api_invalid(self, chat_app):
        """Test handling invalid API command."""
        chat_app.logic.switch_model.return_value = False
        
        result = chat_app._handle_command("api invalid")
        
        assert result is True
        chat_app.ui.print_error.assert_called_once_with("Неизвестный API: invalid")
    
    def test_handle_command_history_on(self, chat_app):
        """Test handling history on command."""
        result = chat_app._handle_command("история вкл")
        
        assert result is True
        chat_app.state.set_history_usage.assert_called_once_with(True)
        chat_app.ui.print_success.assert_called_once_with("История сообщений включена")
    
    def test_handle_command_history_off(self, chat_app):
        """Test handling history off command."""
        result = chat_app._handle_command("история выкл")
        
        assert result is True
        chat_app.state.set_history_usage.assert_called_once_with(False)
        chat_app.ui.print_success.assert_called_once_with("История сообщений выключена")
    
    def test_handle_command_clear_history(self, chat_app):
        """Test handling clear history command."""
        mock_client = MagicMock()
        chat_app.state.current_api = "qwen"
        chat_app.state.local_clients = {"qwen": mock_client}
        
        result = chat_app._handle_clear_history_command()
        
        assert result is True
        mock_client.clear_history.assert_called_once()
        chat_app.ui.print_success.assert_called_once_with("История сообщений очищена")
    
    def test_handle_command_clear_history_not_local(self, chat_app):
        """Test handling clear history command for non-local API."""
        chat_app.state.current_api = "perplexity"
        chat_app.state.local_clients = {}
        
        result = chat_app._handle_clear_history_command()
        
        assert result is True
        chat_app.ui.print_error.assert_called_once_with("История доступна только для локальных моделей")
    
    def test_handle_command_not_handled(self, chat_app):
        """Test handling command that is not handled."""
        result = chat_app._handle_command("unknown command")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_process_message(self, chat_app):
        """Test processing user message."""
        chat_app.logic.parse_temp_override.return_value = (None, "test message")
        chat_app.logic.call_model.return_value = {"response": "test response"}
        chat_app.logic.apply_interactive_temperature.return_value = None
        
        with patch('time.time', side_effect=[0, 1]):  # 1 second duration
            await chat_app._process_message("test message")
        
        chat_app.logic.parse_temp_override.assert_called_once_with("test message")
        chat_app.logic.call_model.assert_called_once()
        chat_app.logic.apply_interactive_temperature.assert_called_once_with("test response")
        chat_app.ui.print_ded_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_with_temp_override(self, chat_app):
        """Test processing message with temperature override."""
        chat_app.logic.parse_temp_override.return_value = (0.8, "test message")
        chat_app.logic.call_model.return_value = {"response": "test response"}
        
        with patch('time.time', side_effect=[0, 1]):
            await chat_app._process_message("temp=0.8 test message")
        
        chat_app.logic.call_model.assert_called_once()
        # Should use the overridden temperature
        call_args = chat_app.logic.call_model.call_args
        assert call_args[0][1] == 0.8  # temperature parameter
