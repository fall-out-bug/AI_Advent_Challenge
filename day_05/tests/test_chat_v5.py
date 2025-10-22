"""
Tests for terminal_chat_v5.py and advice_mode_v5.py

Following Python Zen: "Explicit is better than implicit"
and "Simple is better than complex".
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from terminal_chat_v5 import DedChatV5, LocalModelClient, _contains_any, _normalize_for_trigger
from advice_mode_v5 import AdviceModeV5
from shared_package.clients.base_client import ModelResponse


class TestLocalModelClient:
    """Test LocalModelClient functionality."""
    
    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Test successful chat request."""
        client = LocalModelClient("qwen")
        
        with patch.object(client, 'make_request') as mock_make_request:
            mock_response = ModelResponse(
                response="Test response",
                input_tokens=10,
                response_tokens=5,
                total_tokens=15,
                model_name="qwen",
                response_time=1.0
            )
            mock_make_request.return_value = mock_response
            
            result = await client.chat([
                {"role": "system", "content": "Test system"},
                {"role": "user", "content": "Test message"}
            ])
            
            assert result["response"] == "Test response"
            assert result["input_tokens"] == 10
            assert result["response_tokens"] == 5
            assert result["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_chat_api_error(self):
        """Test chat request with API error."""
        client = LocalModelClient("qwen")
        
        with patch.object(client, 'make_request') as mock_make_request:
            mock_make_request.side_effect = Exception("API Error")
            
            result = await client.chat([
                {"role": "user", "content": "Test message"}
            ])
            
            assert "❌ Ошибка" in result["response"]
            assert result["input_tokens"] == 0
            assert result["response_tokens"] == 0
            assert result["total_tokens"] == 0
    
    @pytest.mark.asyncio
    async def test_chat_connection_error(self):
        """Test chat request with connection error."""
        client = LocalModelClient("qwen")
        
        with patch.object(client, 'make_request') as mock_make_request:
            mock_make_request.side_effect = Exception("Connection failed")
            
            result = await client.chat([
                {"role": "user", "content": "Test message"}
            ])
            
            assert "❌ Ошибка" in result["response"]
            assert result["input_tokens"] == 0
            assert result["response_tokens"] == 0
            assert result["total_tokens"] == 0
    
    def test_clear_history(self):
        """Test clear_history method."""
        client = LocalModelClient("qwen")
        client.conversation_history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"}
        ]
        assert len(client.conversation_history) == 2
        
        client.clear_history()
        assert len(client.conversation_history) == 0
    
    def test_get_history_length(self):
        """Test get_history_length method."""
        client = LocalModelClient("qwen")
        assert client.get_history_length() == 0
        
        client.conversation_history = [
            {"role": "user", "content": "test"}
        ]
        assert client.get_history_length() == 1


class TestDedChatV5:
    """Test DedChatV5 functionality."""
    
    def test_init(self):
        """Test DedChatV5 initialization."""
        chat = DedChatV5()
        assert chat.default_temperature == 0.5
        assert chat.explain_mode is False
        assert chat.current_api is None
        assert chat.use_history is False
        assert len(chat.local_clients) == 3
        assert "qwen" in chat.local_clients
        assert "mistral" in chat.local_clients
        assert "tinyllama" in chat.local_clients
    
    def test_get_model_label_local(self):
        """Test get_model_label for local models."""
        chat = DedChatV5()
        chat.current_api = "qwen"
        assert chat.get_model_label() == "local:qwen"
        
        chat.current_api = "mistral"
        assert chat.get_model_label() == "local:mistral"
    
    def test_get_model_label_external(self):
        """Test get_model_label for external APIs."""
        chat = DedChatV5()
        chat.current_api = "chadgpt"
        assert chat.get_model_label() == "chadgpt:gpt-5-mini"
        
        chat.current_api = "perplexity"
        assert chat.get_model_label() == "perplexity:sonar-pro"
    
    def test_get_api_endpoint_local(self):
        """Test get_api_endpoint for local models."""
        chat = DedChatV5()
        chat.current_api = "qwen"
        assert chat.get_api_endpoint() == "http://localhost:8000"
        
        chat.current_api = "mistral"
        assert chat.get_api_endpoint() == "http://localhost:8001"
    
    def test_get_api_endpoint_external(self):
        """Test get_api_endpoint for external APIs."""
        chat = DedChatV5()
        chat.current_api = "chadgpt"
        assert chat.get_api_endpoint() == "https://ask.chadgpt.ru/api/public/gpt-5-mini"
        
        chat.current_api = "perplexity"
        assert chat.get_api_endpoint() == "https://api.perplexity.ai/chat/completions"
    
    def test_api_switching_local(self):
        """Test API switching to local models."""
        chat = DedChatV5()
        
        # Test switching to local-qwen
        chat.current_api = None
        # Simulate user input "api local-qwen"
        low = "api local-qwen"
        if low.startswith("api "):
            new_api = low.split()[1]
            if new_api.startswith("local-"):
                local_model = new_api[6:]
                if local_model in chat.local_clients:
                    chat.current_api = local_model
        
        assert chat.current_api == "qwen"
        assert chat.get_model_label() == "local:qwen"
    
    def test_api_switching_external(self):
        """Test API switching to external APIs."""
        chat = DedChatV5()
        
        # Test switching to perplexity
        chat.current_api = None
        # Simulate user input "api perplexity"
        low = "api perplexity"
        if low.startswith("api "):
            new_api = low.split()[1]
            if new_api in ("chadgpt", "perplexity"):
                chat.current_api = new_api
        
        assert chat.current_api == "perplexity"
        assert chat.get_model_label() == "perplexity:sonar-pro"
    
    @pytest.mark.asyncio
    async def test_call_local_model(self):
        """Test call_local_model method."""
        chat = DedChatV5()
        chat.current_api = "qwen"
        
        with patch.object(chat.local_clients["qwen"], 'chat') as mock_chat:
            mock_chat.return_value = {
                "response": "Test response",
                "input_tokens": 10,
                "response_tokens": 5,
                "total_tokens": 15
            }
            
            result = await chat.call_local_model("Test message", 0.7)
            
            assert result["response"] == "Test response"
            assert result["input_tokens"] == 10
            mock_chat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_local_model_unknown(self):
        """Test call_local_model with unknown model."""
        chat = DedChatV5()
        chat.current_api = "unknown_model"
        
        result = await chat.call_local_model("Test message", 0.7)
        
        assert "❌ Неизвестная локальная модель: unknown_model" in result["response"]
        assert result["input_tokens"] == 0
        assert result["response_tokens"] == 0
        assert result["total_tokens"] == 0
    
    @pytest.mark.asyncio
    async def test_call_model_routing_local(self):
        """Test call_model routing to local model."""
        chat = DedChatV5()
        chat.current_api = "qwen"
        
        with patch.object(chat, 'call_local_model') as mock_call:
            mock_call.return_value = {
                "response": "Test response",
                "input_tokens": 10,
                "response_tokens": 5,
                "total_tokens": 15
            }
            
            result = await chat.call_model("Test message", 0.7)
            
            assert result["response"] == "Test response"
            assert result["input_tokens"] == 10
            mock_call.assert_called_once_with("Test message", 0.7, None, False)
    
    @pytest.mark.asyncio
    async def test_call_model_routing_external(self):
        """Test call_model routing to external API."""
        chat = DedChatV5()
        chat.current_api = "chadgpt"
        
        with patch.object(chat, 'call_chadgpt') as mock_call:
            mock_call.return_value = "Test response"
            
            result = await chat.call_model("Test message", 0.7)
            
            assert result["response"] == "Test response"
            assert result["input_tokens"] == 0
            assert result["response_tokens"] == 0
            assert result["total_tokens"] == 0
            mock_call.assert_called_once_with("Test message", 0.7, None)


class TestAdviceModeV5:
    """Test AdviceModeV5 functionality."""
    
    def test_init(self):
        """Test AdviceModeV5 initialization."""
        advice = AdviceModeV5("test_key", "qwen")
        assert advice.api_key == "test_key"
        assert advice.api_type == "qwen"
        assert len(advice.local_models) == 3
    
    def test_detect_advice_trigger(self):
        """Test advice trigger detection."""
        advice = AdviceModeV5("test_key")
        
        assert advice.detect_advice_trigger("дай совет") is True
        assert advice.detect_advice_trigger("ДАЙ МНЕ СОВЕТ") is True
        assert advice.detect_advice_trigger("нужен совет") is True
        assert advice.detect_advice_trigger("посоветуй что делать") is True
        assert advice.detect_advice_trigger("привет") is False
    
    def test_extract_topic(self):
        """Test topic extraction."""
        advice = AdviceModeV5("test_key")
        
        assert advice.extract_topic("дай совет по работе") == "по работе"
        assert advice.extract_topic("посоветуй как быть с деньгами") == "с деньгами"
        assert advice.extract_topic("дай совет") == "общая тема"
    
    def test_get_advice_prompt_initial(self):
        """Test initial advice prompt generation."""
        advice = AdviceModeV5("test_key")
        context = {}
        
        prompt = advice.get_advice_prompt("initial", context)
        
        assert "ехидный пожилой дедушка" in prompt
        assert "Спроси ЧТО ИМЕННО его беспокоит" in prompt
        assert "один вопрос и остановись" in prompt
    
    def test_get_advice_prompt_followup(self):
        """Test followup advice prompt generation."""
        advice = AdviceModeV5("test_key")
        context = {
            "question_count": "2",
            "max_questions": "5",
            "user_responses": "ответ1 | ответ2"
        }
        
        prompt = advice.get_advice_prompt("followup", context)
        
        assert "уточняющий вопрос #3" in prompt
        assert "ответ1 | ответ2" in prompt
    
    def test_get_advice_prompt_final(self):
        """Test final advice prompt generation."""
        advice = AdviceModeV5("test_key")
        context = {
            "topic": "работа",
            "user_responses": "ответ1 | ответ2"
        }
        
        prompt = advice.get_advice_prompt("final", context)
        
        assert "Тема совета: работа" in prompt
        assert "финальный совет (3 пункта)" in prompt
    
    @pytest.mark.asyncio
    async def test_get_local_model_response_success(self):
        """Test successful local model response."""
        advice = AdviceModeV5("test_key", "qwen")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Test advice"}
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await advice.get_local_model_response("Test prompt", "qwen")
            
            assert result == "Test advice"
    
    @pytest.mark.asyncio
    async def test_get_local_model_response_unknown_model(self):
        """Test local model response with unknown model."""
        advice = AdviceModeV5("test_key")
        
        result = await advice.get_local_model_response("Test prompt", "unknown")
        
        assert "❌ Неизвестная локальная модель: unknown" in result
    
    @pytest.mark.asyncio
    async def test_get_advice_response_local(self):
        """Test get_advice_response with local model."""
        advice = AdviceModeV5("test_key", "qwen")
        
        with patch.object(advice, 'get_local_model_response') as mock_response:
            mock_response.return_value = "Test response"
            
            result = await advice.get_advice_response("initial", {})
            
            assert result == "Test response"
            mock_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_advice_response_external(self):
        """Test get_advice_response with external API."""
        advice = AdviceModeV5("test_key", "perplexity")
        
        with patch.object(advice, 'get_perplexity_response') as mock_response:
            mock_response.return_value = "Test response"
            
            result = await advice.get_advice_response("initial", {})
            
            assert result == "Test response"
            mock_response.assert_called_once()


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_contains_any(self):
        """Test _contains_any function."""
        assert _contains_any("hello world", ["hello", "test"]) is True
        assert _contains_any("hello world", ["test", "foo"]) is False
        assert _contains_any("HELLO WORLD", ["hello", "test"]) is True
        assert _contains_any("", ["hello"]) is False
    
    def test_normalize_for_trigger(self):
        """Test _normalize_for_trigger function."""
        assert _normalize_for_trigger("Hello, World!") == "hello world"
        assert _normalize_for_trigger("Привет-мир") == "привет мир"
        assert _normalize_for_trigger("") == ""
        assert _normalize_for_trigger("Test—with—dashes") == "test with dashes"


if __name__ == "__main__":
    pytest.main([__file__])
