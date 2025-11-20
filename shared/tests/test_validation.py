"""
Tests for input validation models.
"""

import pytest
from pydantic import ValidationError
from shared_package.validation.models import (
    ChatMessage,
    ChatRequest,
    ModelAvailabilityRequest,
    ModelRequest,
    ModelResponse,
)
from shared_package.validation.models import ValidationError as CustomValidationError
from shared_package.validation.models import (
    sanitize_input,
    validate_chat_request,
    validate_model_request,
    validate_model_response,
)


class TestModelRequest:
    """Test ModelRequest validation."""

    def test_valid_model_request(self):
        """Test valid model request."""
        request = ModelRequest(
            model_name="qwen", prompt="Hello, world!", max_tokens=100, temperature=0.7
        )

        assert request.model_name == "qwen"
        assert request.prompt == "Hello, world!"
        assert request.max_tokens == 100
        assert request.temperature == 0.7

    def test_model_request_defaults(self):
        """Test model request with defaults."""
        request = ModelRequest(model_name="mistral", prompt="Test prompt")

        assert request.model_name == "mistral"
        assert request.prompt == "Test prompt"
        assert request.max_tokens == 10000
        assert request.temperature == 0.7

    def test_model_name_validation(self):
        """Test model name validation."""
        # Valid names
        valid_names = [
            "qwen",
            "mistral",
            "tinyllama",
            "perplexity",
            "chadgpt",
            "model-1",
            "model_1",
        ]
        for name in valid_names:
            request = ModelRequest(model_name=name, prompt="test")
            assert request.model_name == name.lower()

        # Invalid names
        invalid_names = ["model name", "model@name", "model.name", "model/name", ""]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                ModelRequest(model_name=name, prompt="test")

    def test_prompt_validation(self):
        """Test prompt validation."""
        # Valid prompts
        valid_prompts = ["Hello", "What is AI?", "Explain quantum computing"]
        for prompt in valid_prompts:
            request = ModelRequest(model_name="qwen", prompt=prompt)
            assert request.prompt == prompt

        # Empty prompt
        with pytest.raises(ValidationError):
            ModelRequest(model_name="qwen", prompt="")

        # Too long prompt
        long_prompt = "x" * 50001
        with pytest.raises(ValidationError):
            ModelRequest(model_name="qwen", prompt=long_prompt)

    def test_prompt_sanitization(self):
        """Test prompt sanitization."""
        # Whitespace normalization
        request = ModelRequest(model_name="qwen", prompt="  Hello   world  ")
        assert request.prompt == "Hello world"

        # Dangerous content detection
        dangerous_prompts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "onload=alert('xss')",
            "onerror=alert('xss')",
        ]

        for prompt in dangerous_prompts:
            with pytest.raises(ValidationError, match="potentially harmful content"):
                ModelRequest(model_name="qwen", prompt=prompt)

    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        # Valid values
        valid_tokens = [1, 100, 1000, 10000, 100000]
        for tokens in valid_tokens:
            request = ModelRequest(model_name="qwen", prompt="test", max_tokens=tokens)
            assert request.max_tokens == tokens

        # Invalid values
        invalid_tokens = [0, -1, 100001]
        for tokens in invalid_tokens:
            with pytest.raises(ValidationError):
                ModelRequest(model_name="qwen", prompt="test", max_tokens=tokens)

    def test_temperature_validation(self):
        """Test temperature validation."""
        # Valid values
        valid_temps = [0.0, 0.5, 1.0, 1.5, 2.0]
        for temp in valid_temps:
            request = ModelRequest(model_name="qwen", prompt="test", temperature=temp)
            assert request.temperature == temp

        # Invalid values
        invalid_temps = [-0.1, 2.1, 10.0]
        for temp in invalid_temps:
            with pytest.raises(ValidationError):
                ModelRequest(model_name="qwen", prompt="test", temperature=temp)


class TestModelResponse:
    """Test ModelResponse validation."""

    def test_valid_model_response(self):
        """Test valid model response."""
        response = ModelResponse(
            response="Hello, world!",
            input_tokens=10,
            response_tokens=5,
            total_tokens=15,
            model_name="qwen",
            response_time=1.5,
        )

        assert response.response == "Hello, world!"
        assert response.input_tokens == 10
        assert response.response_tokens == 5
        assert response.total_tokens == 15
        assert response.model_name == "qwen"
        assert response.response_time == 1.5

    def test_response_sanitization(self):
        """Test response sanitization."""
        response = ModelResponse(
            response="  Hello   world  ",
            input_tokens=10,
            response_tokens=5,
            total_tokens=15,
            model_name="qwen",
            response_time=1.5,
        )

        assert response.response == "Hello world"

    def test_total_tokens_validation(self):
        """Test total_tokens validation."""
        # Valid total tokens
        response = ModelResponse(
            response="test",
            input_tokens=10,
            response_tokens=5,
            total_tokens=15,
            model_name="qwen",
            response_time=1.0,
        )
        assert response.total_tokens == 15

        # Invalid total tokens
        with pytest.raises(
            ValidationError, match="must equal input_tokens \\+ response_tokens"
        ):
            ModelResponse(
                response="test",
                input_tokens=10,
                response_tokens=5,
                total_tokens=20,  # Should be 15
                model_name="qwen",
                response_time=1.0,
            )


class TestChatMessage:
    """Test ChatMessage validation."""

    def test_valid_chat_message(self):
        """Test valid chat message."""
        message = ChatMessage(role="user", content="Hello!")

        assert message.role == "user"
        assert message.content == "Hello!"

    def test_role_validation(self):
        """Test role validation."""
        # Valid roles
        valid_roles = ["system", "user", "assistant"]
        for role in valid_roles:
            message = ChatMessage(role=role, content="test")
            assert message.role == role

        # Invalid roles
        invalid_roles = ["admin", "bot", "unknown", ""]
        for role in invalid_roles:
            with pytest.raises(ValidationError):
                ChatMessage(role=role, content="test")

    def test_content_validation(self):
        """Test content validation."""
        # Valid content
        message = ChatMessage(role="user", content="Hello, world!")
        assert message.content == "Hello, world!"

        # Empty content
        with pytest.raises(ValidationError):
            ChatMessage(role="user", content="")

        # Dangerous content
        with pytest.raises(ValidationError, match="potentially harmful content"):
            ChatMessage(role="user", content="<script>alert('xss')</script>")


class TestChatRequest:
    """Test ChatRequest validation."""

    def test_valid_chat_request(self):
        """Test valid chat request."""
        messages = [
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello!"),
        ]

        request = ChatRequest(messages=messages)

        assert len(request.messages) == 2
        assert request.messages[0].role == "system"
        assert request.messages[1].role == "user"

    def test_empty_messages(self):
        """Test empty messages list."""
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            ChatRequest(messages=[])

    def test_first_message_validation(self):
        """Test first message must be system or user."""
        messages = [ChatMessage(role="assistant", content="Hello!")]

        with pytest.raises(
            ValidationError, match="First message must be from system or user"
        ):
            ChatRequest(messages=messages)

    def test_conversation_length_limit(self):
        """Test conversation length limit."""
        # Create messages that exceed the limit when combined
        # Each message is 50000 chars, so 2 messages = 100000 chars (at the limit)
        # We need 3 messages to exceed the limit
        long_content = "x" * 50000
        messages = [
            ChatMessage(role="user", content=long_content),
            ChatMessage(role="assistant", content=long_content),
            ChatMessage(
                role="user", content="extra content"
            ),  # This pushes it over the limit
        ]

        with pytest.raises(
            ValidationError, match="Total conversation length exceeds limit"
        ):
            ChatRequest(messages=messages)


class TestValidationFunctions:
    """Test validation helper functions."""

    def test_validate_model_request(self):
        """Test validate_model_request function."""
        data = {
            "model_name": "qwen",
            "prompt": "Hello!",
            "max_tokens": 100,
            "temperature": 0.7,
        }

        request = validate_model_request(data)
        assert isinstance(request, ModelRequest)
        assert request.model_name == "qwen"

    def test_validate_model_request_invalid(self):
        """Test validate_model_request with invalid data."""
        data = {
            "model_name": "",  # Invalid
            "prompt": "Hello!",
            "max_tokens": 100,
            "temperature": 0.7,
        }

        with pytest.raises(CustomValidationError, match="Validation failed"):
            validate_model_request(data)

    def test_validate_chat_request(self):
        """Test validate_chat_request function."""
        data = {
            "messages": [{"role": "user", "content": "Hello!"}],
            "max_tokens": 100,
            "temperature": 0.7,
        }

        request = validate_chat_request(data)
        assert isinstance(request, ChatRequest)
        assert len(request.messages) == 1

    def test_validate_model_response(self):
        """Test validate_model_response function."""
        data = {
            "response": "Hello!",
            "input_tokens": 10,
            "response_tokens": 5,
            "total_tokens": 15,
            "model_name": "qwen",
            "response_time": 1.0,
        }

        response = validate_model_response(data)
        assert isinstance(response, ModelResponse)
        assert response.response == "Hello!"


class TestSanitizeInput:
    """Test sanitize_input function."""

    def test_sanitize_normal_text(self):
        """Test sanitizing normal text."""
        text = "Hello, world!"
        result = sanitize_input(text)
        assert result == "Hello, world!"

    def test_sanitize_whitespace(self):
        """Test sanitizing excessive whitespace."""
        text = "  Hello   world  "
        result = sanitize_input(text)
        assert result == "Hello world"

    def test_sanitize_dangerous_chars(self):
        """Test sanitizing dangerous characters."""
        text = "Hello <script>alert('xss')</script> world"
        result = sanitize_input(text)
        assert result == "Hello scriptalert(xss)/script world"

    def test_sanitize_empty_text(self):
        """Test sanitizing empty text."""
        assert sanitize_input("") == ""
        assert sanitize_input(None) == ""

    def test_sanitize_multiline_text(self):
        """Test sanitizing multiline text."""
        text = "Line 1\n\nLine 2\t\tTab"
        result = sanitize_input(text)
        assert result == "Line 1 Line 2 Tab"
