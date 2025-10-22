"""
Tests for ui/terminal_ui.py module.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

import pytest
from unittest.mock import MagicMock, patch
from io import StringIO
import sys

from ui.terminal_ui import TerminalUI


class TestTerminalUI:
    """Test TerminalUI functionality."""
    
    @pytest.fixture
    def mock_state(self):
        """Create mock chat state."""
        state = MagicMock()
        state.current_api = "perplexity"
        state.default_temperature = 0.5
        state.explain_mode = False
        state.local_clients = {}
        return state
    
    @pytest.fixture
    def terminal_ui(self, mock_state):
        """Create TerminalUI instance."""
        return TerminalUI(mock_state)
    
    def test_init(self, mock_state):
        """Test TerminalUI initialization."""
        ui = TerminalUI(mock_state)
        
        assert ui.state == mock_state
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_welcome(self, mock_stdout, terminal_ui):
        """Test welcome message printing."""
        terminal_ui.print_welcome()
        
        output = mock_stdout.getvalue()
        assert "ДЕДУШКА AI v5" in output
        assert "Команды:" in output
        assert "Триггеры авто‑температуры" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_ded_message_simple(self, mock_stdout, terminal_ui):
        """Test printing simple message."""
        terminal_ui.print_ded_message("Test message")
        
        output = mock_stdout.getvalue()
        assert "👴 Дедушка: Test message" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_ded_message_with_temp(self, mock_stdout, terminal_ui):
        """Test printing message with temperature."""
        terminal_ui.state.explain_mode = True
        
        terminal_ui.print_ded_message("Test message", 0.7)
        
        output = mock_stdout.getvalue()
        assert "👴 Дедушка [T=0.70" in output
        assert "Test message" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_debug_info_explain_mode(self, mock_stdout, terminal_ui):
        """Test printing debug info in explain mode."""
        terminal_ui.state.explain_mode = True
        
        reply_data = {
            "response": "Test response",
            "total_tokens": 100
        }
        
        terminal_ui.print_debug_info(
            "user message", reply_data, 0.7, "system prompt", 1500
        )
        
        output = mock_stdout.getvalue()
        assert "🔍 DEBUG" in output
        assert "Model:" in output
        assert "Temperature: 0.700" in output
        assert "Duration: 1500ms" in output
        assert "Tokens: 100" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_debug_info_normal_mode(self, mock_stdout, terminal_ui):
        """Test printing debug info in normal mode (should not print)."""
        terminal_ui.state.explain_mode = False
        
        reply_data = {"response": "Test response"}
        
        terminal_ui.print_debug_info(
            "user message", reply_data, 0.7, None, 1500
        )
        
        output = mock_stdout.getvalue()
        assert output == ""  # Should not print anything
    
    def test_get_model_label_perplexity(self, terminal_ui):
        """Test getting model label for Perplexity."""
        terminal_ui.state.current_api = "perplexity"
        
        label = terminal_ui._get_model_label()
        
        assert label == "perplexity:sonar-pro"
    
    def test_get_model_label_chadgpt(self, terminal_ui):
        """Test getting model label for ChadGPT."""
        terminal_ui.state.current_api = "chadgpt"
        
        label = terminal_ui._get_model_label()
        
        assert label == "chadgpt:gpt-5-mini"
    
    def test_get_model_label_local(self, terminal_ui):
        """Test getting model label for local model."""
        terminal_ui.state.current_api = "qwen"
        terminal_ui.state.local_clients = {"qwen": MagicMock()}
        
        label = terminal_ui._get_model_label()
        
        assert label == "local:qwen"
    
    def test_get_api_endpoint_perplexity(self, terminal_ui):
        """Test getting API endpoint for Perplexity."""
        terminal_ui.state.current_api = "perplexity"
        
        endpoint = terminal_ui._get_api_endpoint()
        
        assert endpoint == "https://api.perplexity.ai/chat/completions"
    
    def test_get_api_endpoint_chadgpt(self, terminal_ui):
        """Test getting API endpoint for ChadGPT."""
        terminal_ui.state.current_api = "chadgpt"
        
        endpoint = terminal_ui._get_api_endpoint()
        
        assert endpoint == "https://ask.chadgpt.ru/api/public/gpt-5-mini"
    
    @patch('builtins.input', return_value="test input")
    def test_get_user_input_normal(self, mock_input, terminal_ui):
        """Test getting user input in normal mode."""
        result = terminal_ui.get_user_input()
        
        assert result == "test input"
    
    @patch('builtins.input', return_value="test input")
    def test_get_user_input_explain_mode(self, mock_input, terminal_ui):
        """Test getting user input in explain mode."""
        terminal_ui.state.explain_mode = True
        
        result = terminal_ui.get_user_input()
        
        assert result == "test input"
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_error(self, mock_stdout, terminal_ui):
        """Test printing error message."""
        terminal_ui.print_error("Test error")
        
        output = mock_stdout.getvalue()
        assert "❌ Test error" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_success(self, mock_stdout, terminal_ui):
        """Test printing success message."""
        terminal_ui.print_success("Test success")
        
        output = mock_stdout.getvalue()
        assert "✅ Test success" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_info(self, mock_stdout, terminal_ui):
        """Test printing info message."""
        terminal_ui.print_info("Test info")
        
        output = mock_stdout.getvalue()
        assert "ℹ️  Test info" in output
