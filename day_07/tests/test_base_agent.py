"""Tests for base agent functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from agents.core.base_agent import BaseAgent


class TestBaseAgent:
    """Test base agent functionality."""

    def setup_method(self):
        """Set up test agent."""
        self.agent = BaseAgent()

    def test_init(self):
        """Test agent initialization."""
        assert self.agent is not None
        assert hasattr(self.agent, 'model_name')
        assert hasattr(self.agent, 'timeout')

    def test_init_with_custom_params(self):
        """Test agent initialization with custom parameters."""
        agent = BaseAgent(model_name="mistral", timeout=30.0)
        assert agent.model_name == "mistral"
        assert agent.timeout == 30.0

    @patch("agents.core.base_agent.ModelClientAdapter")
    async def test_call_model_success(self, mock_adapter_class):
        """Test successful model call."""
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_adapter.make_request.return_value = {
            "response": "def test(): pass",
            "input_tokens": 50,
            "response_tokens": 100,
            "total_tokens": 150
        }
        mock_adapter_class.return_value = mock_adapter
        
        agent = BaseAgent()
        agent._model_adapter = mock_adapter

        result = await agent._call_model(
            prompt="Create a test function",
            max_tokens=1000,
            temperature=0.7
        )

        assert result["response"] == "def test(): pass"
        assert result["input_tokens"] == 50
        assert result["response_tokens"] == 100
        assert result["total_tokens"] == 150

    @patch("agents.core.base_agent.ModelClientAdapter")
    async def test_call_model_error(self, mock_adapter_class):
        """Test model call with error."""
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_adapter.make_request.side_effect = Exception("Model error")
        mock_adapter_class.return_value = mock_adapter
        
        agent = BaseAgent()
        agent._model_adapter = mock_adapter

        with pytest.raises(Exception, match="Model error"):
            await agent._call_model(
                prompt="Create a test function",
                max_tokens=1000,
                temperature=0.7
            )

    def test_get_model_adapter(self):
        """Test getting model adapter."""
        adapter = self.agent._get_model_adapter()
        assert adapter is not None
        assert hasattr(adapter, 'model_name')

    def test_get_model_adapter_custom_model(self):
        """Test getting model adapter with custom model."""
        agent = BaseAgent(model_name="qwen")
        adapter = agent._get_model_adapter()
        assert adapter.model_name == "qwen"

    def test_prepare_prompt_basic(self):
        """Test basic prompt preparation."""
        prompt = self.agent._prepare_prompt("Create a function")
        assert isinstance(prompt, str)
        assert "Create a function" in prompt

    def test_prepare_prompt_with_context(self):
        """Test prompt preparation with context."""
        context = {"language": "python", "requirements": ["type hints"]}
        prompt = self.agent._prepare_prompt("Create a function", context=context)
        assert isinstance(prompt, str)
        assert "Create a function" in prompt

    def test_extract_code_from_response(self):
        """Test code extraction from response."""
        response = {
            "response": "Here's the code:\n```python\ndef test(): pass\n```\nThat's it!"
        }
        
        code = self.agent._extract_code_from_response(response)
        assert code == "def test(): pass"

    def test_extract_code_from_response_no_code(self):
        """Test code extraction when no code blocks found."""
        response = {
            "response": "This is just text without code blocks."
        }
        
        code = self.agent._extract_code_from_response(response)
        assert code == "This is just text without code blocks."

    def test_extract_code_from_response_multiple_blocks(self):
        """Test code extraction with multiple code blocks."""
        response = {
            "response": "First:\n```python\ndef first(): pass\n```\nSecond:\n```python\ndef second(): pass\n```"
        }
        
        code = self.agent._extract_code_from_response(response)
        assert "def first(): pass" in code
        assert "def second(): pass" in code

    def test_validate_code_basic(self):
        """Test basic code validation."""
        code = "def test(): pass"
        is_valid = self.agent._validate_code(code)
        assert is_valid is True

    def test_validate_code_empty(self):
        """Test validation of empty code."""
        code = ""
        is_valid = self.agent._validate_code(code)
        assert is_valid is False

    def test_validate_code_whitespace_only(self):
        """Test validation of whitespace-only code."""
        code = "   \n  \t  \n  "
        is_valid = self.agent._validate_code(code)
        assert is_valid is False

    def test_validate_code_with_imports(self):
        """Test validation of code with imports."""
        code = "import os\n\ndef test(): pass"
        is_valid = self.agent._validate_code(code)
        assert is_valid is True

    def test_calculate_tokens_estimate(self):
        """Test token estimation."""
        text = "def test(): pass"
        tokens = self.agent._calculate_tokens_estimate(text)
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_calculate_tokens_estimate_empty(self):
        """Test token estimation for empty text."""
        text = ""
        tokens = self.agent._calculate_tokens_estimate(text)
        assert tokens == 0

    def test_format_response_time(self):
        """Test response time formatting."""
        start_time = datetime.now()
        end_time = start_time
        
        formatted_time = self.agent._format_response_time(start_time, end_time)
        assert isinstance(formatted_time, str)
        assert "0.0" in formatted_time or "0.00" in formatted_time

    def test_format_response_time_with_delay(self):
        """Test response time formatting with actual delay."""
        start_time = datetime.now()
        # Simulate some processing time
        import time
        time.sleep(0.01)  # 10ms
        end_time = datetime.now()
        
        formatted_time = self.agent._format_response_time(start_time, end_time)
        assert isinstance(formatted_time, str)
        assert float(formatted_time) > 0

    def test_create_metadata(self):
        """Test metadata creation."""
        code = "def test(): pass"
        tokens_used = 100
        
        metadata = self.agent._create_metadata(code, tokens_used)
        assert isinstance(metadata, dict)
        assert "complexity" in metadata
        assert "lines_of_code" in metadata
        assert "estimated_time" in metadata
        assert "dependencies" in metadata

    def test_create_metadata_with_dependencies(self):
        """Test metadata creation with dependencies."""
        code = "import os\nimport sys\n\ndef test(): pass"
        tokens_used = 150
        
        metadata = self.agent._create_metadata(code, tokens_used)
        assert "os" in metadata["dependencies"]
        assert "sys" in metadata["dependencies"]

    def test_detect_complexity_simple(self):
        """Test complexity detection for simple code."""
        code = "def test(): pass"
        complexity = self.agent._detect_complexity(code)
        assert complexity in ["low", "medium", "high"]

    def test_detect_complexity_complex(self):
        """Test complexity detection for complex code."""
        code = """
def complex_function(data):
    result = []
    for item in data:
        if item > 0:
            try:
                processed = item * 2
                if processed > 100:
                    result.append(processed)
                else:
                    result.append(item)
            except Exception as e:
                print(f"Error: {e}")
    return result
"""
        complexity = self.agent._detect_complexity(code)
        assert complexity in ["low", "medium", "high"]

    def test_extract_dependencies(self):
        """Test dependency extraction."""
        code = "import os\nimport sys\nfrom typing import List\n\ndef test(): pass"
        dependencies = self.agent._extract_dependencies(code)
        assert "os" in dependencies
        assert "sys" in dependencies
        assert "typing" in dependencies

    def test_extract_dependencies_no_imports(self):
        """Test dependency extraction with no imports."""
        code = "def test(): pass"
        dependencies = self.agent._extract_dependencies(code)
        assert dependencies == []

    def test_extract_dependencies_from_imports(self):
        """Test dependency extraction from 'from' imports."""
        code = "from typing import List, Dict\nfrom os import path\n\ndef test(): pass"
        dependencies = self.agent._extract_dependencies(code)
        assert "typing" in dependencies
        assert "os" in dependencies
