"""
Tests for token_service refactoring.

This module tests the refactored token service components:
TokenService, TokenServiceHandler, and related functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from services.token_service import (
    TokenService,
    TokenCountRequest,
    TokenCountResponse,
    CompressionRequest,
    CompressionResponse,
    BatchTokenCountRequest,
    BatchTokenCountResponse
)
from api.handlers.token_handler import TokenServiceHandler
from core.validators.request_validator import RequestValidator
from core.interfaces.protocols import TokenCounterProtocol
from models.data_models import TokenInfo, CompressionResult


class TestTokenService:
    """Test TokenService business logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_token_counter = Mock(spec=TokenCounterProtocol)
        self.mock_token_counter.count_tokens.return_value = TokenInfo(
            count=100,
            model_name="starcoder",
            estimated_cost=0.01
        )
        self.mock_token_counter.get_available_models.return_value = ["starcoder", "mistral"]
        
        self.service = TokenService(token_counter=self.mock_token_counter)

    @pytest.mark.asyncio
    async def test_count_tokens_success(self):
        """Test successful token counting."""
        request = TokenCountRequest(text="Hello world", model_name="starcoder")
        
        result = await self.service.count_tokens(request)
        
        assert result.count == 100
        assert result.model_name == "starcoder"
        assert result.estimated_cost == 0.01
        self.mock_token_counter.count_tokens.assert_called_once_with("Hello world", "starcoder")

    @pytest.mark.asyncio
    async def test_count_tokens_empty_text(self):
        """Test token counting with empty text."""
        request = TokenCountRequest(text="", model_name="starcoder")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await self.service.count_tokens(request)

    @pytest.mark.asyncio
    async def test_count_tokens_whitespace_only(self):
        """Test token counting with whitespace-only text."""
        request = TokenCountRequest(text="   ", model_name="starcoder")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await self.service.count_tokens(request)

    @pytest.mark.asyncio
    async def test_count_tokens_error(self):
        """Test token counting with error."""
        self.mock_token_counter.count_tokens.side_effect = Exception("Token counting failed")
        request = TokenCountRequest(text="Hello world", model_name="starcoder")
        
        with pytest.raises(RuntimeError, match="Failed to count tokens"):
            await self.service.count_tokens(request)

    @pytest.mark.asyncio
    async def test_batch_count_tokens_success(self):
        """Test successful batch token counting."""
        request = BatchTokenCountRequest(
            texts=["Hello", "World", "Test"],
            model_name="starcoder"
        )
        
        result = await self.service.batch_count_tokens(request)
        
        assert len(result.results) == 3
        assert all(r.count == 100 for r in result.results)
        assert self.mock_token_counter.count_tokens.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_count_tokens_empty_list(self):
        """Test batch token counting with empty list."""
        request = BatchTokenCountRequest(texts=[], model_name="starcoder")
        
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            await self.service.batch_count_tokens(request)

    @pytest.mark.asyncio
    async def test_batch_count_tokens_skip_empty_texts(self):
        """Test batch token counting skips empty texts."""
        request = BatchTokenCountRequest(
            texts=["Hello", "", "World"],
            model_name="starcoder"
        )
        
        result = await self.service.batch_count_tokens(request)
        
        # Should skip empty text, so only 2 results
        assert len(result.results) == 2
        assert self.mock_token_counter.count_tokens.call_count == 2

    @pytest.mark.asyncio
    async def test_compress_text_success(self):
        """Test successful text compression."""
        # Mock compressor
        mock_compressor = Mock()
        mock_compressor.compress.return_value = CompressionResult(
            original_text="Hello world",
            compressed_text="Hello",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="extractive"
        )
        
        with patch.object(self.service, 'extractive_compressor', mock_compressor):
            request = CompressionRequest(
                text="Hello world",
                max_tokens=50,
                model_name="starcoder",
                strategy="extractive"
            )
            
            result = await self.service.compress_text(request)
            
            assert result.compression_ratio == 0.5
            assert result.strategy_used == "extractive"
            mock_compressor.compress.assert_called_once()

    @pytest.mark.asyncio
    async def test_compress_text_empty_text(self):
        """Test text compression with empty text."""
        request = CompressionRequest(
            text="",
            max_tokens=50,
            model_name="starcoder",
            strategy="extractive"
        )
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await self.service.compress_text(request)

    @pytest.mark.asyncio
    async def test_compress_text_invalid_max_tokens(self):
        """Test text compression with invalid max tokens."""
        request = CompressionRequest(
            text="Hello world",
            max_tokens=0,
            model_name="starcoder",
            strategy="extractive"
        )
        
        with pytest.raises(ValueError, match="Max tokens must be positive"):
            await self.service.compress_text(request)

    @pytest.mark.asyncio
    async def test_compress_text_invalid_strategy(self):
        """Test text compression with invalid strategy."""
        request = CompressionRequest(
            text="Hello world",
            max_tokens=50,
            model_name="starcoder",
            strategy="invalid"
        )
        
        with pytest.raises(RuntimeError, match="Failed to compress text"):
            await self.service.compress_text(request)

    @pytest.mark.asyncio
    async def test_preview_compression_success(self):
        """Test successful compression preview."""
        # Mock compressors
        mock_extractive = Mock()
        mock_extractive.compress.return_value = CompressionResult(
            original_text="Hello world",
            compressed_text="Hello",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="extractive"
        )
        
        mock_semantic = Mock()
        mock_semantic.compress.return_value = CompressionResult(
            original_text="Hello world",
            compressed_text="World",
            original_tokens=100,
            compressed_tokens=60,
            compression_ratio=0.6,
            strategy_used="semantic"
        )
        
        with patch.object(self.service, 'extractive_compressor', mock_extractive), \
             patch.object(self.service, 'semantic_chunker', mock_semantic):
            
            request = CompressionRequest(
                text="Hello world",
                max_tokens=50,
                model_name="starcoder",
                strategy="preview"
            )
            
            result = await self.service.preview_compression(request)
            
            assert "extractive" in result
            assert "semantic" in result
            assert result["extractive"]["compression_ratio"] == 0.5
            assert result["semantic"]["compression_ratio"] == 0.6

    @pytest.mark.asyncio
    async def test_preview_compression_empty_text(self):
        """Test compression preview with empty text."""
        request = CompressionRequest(
            text="",
            max_tokens=50,
            model_name="starcoder",
            strategy="preview"
        )
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await self.service.preview_compression(request)

    def test_get_available_models(self):
        """Test getting available models."""
        models = self.service.get_available_models()
        
        assert models == ["starcoder", "mistral"]
        self.mock_token_counter.get_available_models.assert_called_once()

    def test_get_available_strategies(self):
        """Test getting available strategies."""
        strategies = self.service.get_available_strategies()
        
        assert "strategies" in strategies
        assert "descriptions" in strategies
        assert "extractive" in strategies["strategies"]
        assert "semantic" in strategies["strategies"]

    def test_create_preview(self):
        """Test preview text creation."""
        long_text = "A" * 300
        preview = self.service._create_preview(long_text, max_length=200)
        
        assert len(preview) == 203  # 200 + "..."
        assert preview.endswith("...")

    def test_create_preview_short_text(self):
        """Test preview text creation with short text."""
        short_text = "Hello"
        preview = self.service._create_preview(short_text, max_length=200)
        
        assert preview == "Hello"


class TestTokenServiceHandler:
    """Test TokenServiceHandler HTTP handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock(spec=TokenService)
        self.mock_service.count_tokens = AsyncMock()
        self.mock_service.batch_count_tokens = AsyncMock()
        self.mock_service.compress_text = AsyncMock()
        self.mock_service.preview_compression = AsyncMock()
        self.mock_service.get_available_models.return_value = ["starcoder", "mistral"]
        self.mock_service.get_available_strategies.return_value = {
            "strategies": ["extractive", "semantic"],
            "descriptions": {"extractive": "TF-IDF based", "semantic": "Semantic chunking"}
        }
        
        self.handler = TokenServiceHandler(service=self.mock_service)

    def test_create_app(self):
        """Test FastAPI app creation."""
        app = self.handler.create_app()
        
        assert app is not None
        assert app.title == "Token Analysis Service"

    @pytest.mark.asyncio
    async def test_handle_health_check_success(self):
        """Test successful health check."""
        result = await self.handler._handle_health_check()
        
        assert result["status"] == "healthy"
        assert result["service"] == "token-analysis"
        assert "available_models" in result

    @pytest.mark.asyncio
    async def test_handle_health_check_error(self):
        """Test health check with error."""
        self.mock_service.get_available_models.side_effect = Exception("Service error")
        
        with pytest.raises(Exception):  # HTTPException from FastAPI
            await self.handler._handle_health_check()

    @pytest.mark.asyncio
    async def test_handle_count_tokens_success(self):
        """Test successful token counting request handling."""
        from api.handlers.token_handler import TokenCountRequestModel
        
        request = TokenCountRequestModel(text="Hello world", model_name="starcoder")
        self.mock_service.count_tokens.return_value = TokenCountResponse(
            count=100,
            model_name="starcoder",
            estimated_cost=0.01
        )
        
        result = await self.handler._handle_count_tokens(request)
        
        assert result.count == 100
        assert result.model_name == "starcoder"
        assert result.estimated_cost == 0.01

    @pytest.mark.asyncio
    async def test_handle_count_tokens_validation_error(self):
        """Test token counting with validation error."""
        from api.handlers.token_handler import TokenCountRequestModel
        from fastapi import HTTPException
        
        # Pydantic will validate and reject empty text before reaching our handler
        with pytest.raises(Exception):  # Pydantic validation error
            TokenCountRequestModel(text="", model_name="starcoder")

    @pytest.mark.asyncio
    async def test_handle_count_tokens_service_error(self):
        """Test token counting with service error."""
        from api.handlers.token_handler import TokenCountRequestModel
        
        request = TokenCountRequestModel(text="Hello world", model_name="starcoder")
        self.mock_service.count_tokens.side_effect = Exception("Service error")
        
        with pytest.raises(Exception):  # HTTPException from FastAPI
            await self.handler._handle_count_tokens(request)

    @pytest.mark.asyncio
    async def test_handle_batch_count_tokens_success(self):
        """Test successful batch token counting request handling."""
        from api.handlers.token_handler import BatchTokenCountRequestModel
        
        request = BatchTokenCountRequestModel(
            texts=["Hello", "World"],
            model_name="starcoder"
        )
        self.mock_service.batch_count_tokens.return_value = BatchTokenCountResponse(
            results=[
                TokenCountResponse(count=50, model_name="starcoder"),
                TokenCountResponse(count=60, model_name="starcoder")
            ]
        )
        
        result = await self.handler._handle_count_tokens_batch(request)
        
        assert len(result.results) == 2
        assert result.results[0].count == 50
        assert result.results[1].count == 60

    @pytest.mark.asyncio
    async def test_handle_compress_text_success(self):
        """Test successful text compression request handling."""
        from api.handlers.token_handler import CompressionRequestModel
        
        request = CompressionRequestModel(
            text="Hello world",
            max_tokens=50,
            model_name="starcoder",
            strategy="truncation"  # Use valid strategy
        )
        self.mock_service.compress_text.return_value = CompressionResponse(
            original_text="Hello world",
            compressed_text="Hello",
            original_tokens=100,
            compressed_tokens=50,
            compression_ratio=0.5,
            strategy_used="truncation"
        )
        
        result = await self.handler._handle_compress_text(request)
        
        assert result.compression_ratio == 0.5
        assert result.strategy_used == "truncation"

    @pytest.mark.asyncio
    async def test_handle_preview_compression_success(self):
        """Test successful compression preview request handling."""
        from api.handlers.token_handler import CompressionRequestModel
        
        request = CompressionRequestModel(
            text="Hello world",
            max_tokens=50,
            model_name="starcoder",
            strategy="preview"
        )
        self.mock_service.preview_compression.return_value = {
            "extractive": {"compression_ratio": 0.5},
            "semantic": {"compression_ratio": 0.6}
        }
        
        result = await self.handler._handle_preview_compression(request)
        
        assert "extractive" in result
        assert "semantic" in result

    @pytest.mark.asyncio
    async def test_handle_get_available_models(self):
        """Test getting available models."""
        result = await self.handler._handle_get_available_models()
        
        assert "models" in result
        assert result["models"] == ["starcoder", "mistral"]

    @pytest.mark.asyncio
    async def test_handle_get_available_strategies(self):
        """Test getting available strategies."""
        result = await self.handler._handle_get_available_strategies()
        
        assert "strategies" in result
        assert "descriptions" in result


class TestRequestValidator:
    """Test RequestValidator functionality."""

    def test_validate_token_count_request_success(self):
        """Test successful token count request validation."""
        RequestValidator.validate_token_count_request("Hello world", "starcoder")

    def test_validate_token_count_request_empty_text(self):
        """Test token count request validation with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            RequestValidator.validate_token_count_request("", "starcoder")

    def test_validate_token_count_request_empty_model(self):
        """Test token count request validation with empty model."""
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            RequestValidator.validate_token_count_request("Hello", "")

    def test_validate_batch_token_count_request_success(self):
        """Test successful batch token count request validation."""
        RequestValidator.validate_batch_token_count_request(
            ["Hello", "World"], "starcoder"
        )

    def test_validate_batch_token_count_request_empty_list(self):
        """Test batch token count request validation with empty list."""
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            RequestValidator.validate_batch_token_count_request([], "starcoder")

    def test_validate_batch_token_count_request_invalid_text(self):
        """Test batch token count request validation with invalid text."""
        with pytest.raises(ValueError, match="Invalid text at index 1"):
            RequestValidator.validate_batch_token_count_request(
                ["Hello", ""], "starcoder"
            )

    def test_validate_compression_request_success(self):
        """Test successful compression request validation."""
        RequestValidator.validate_compression_request(
            "Hello world", 50, "starcoder", "truncation"  # Use valid strategy
        )

    def test_validate_compression_request_empty_text(self):
        """Test compression request validation with empty text."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            RequestValidator.validate_compression_request(
                "", 50, "starcoder", "extractive"
            )

    def test_validate_compression_request_invalid_max_tokens(self):
        """Test compression request validation with invalid max tokens."""
        with pytest.raises(ValueError, match="Max tokens must be >= 1"):
            RequestValidator.validate_compression_request(
                "Hello world", 0, "starcoder", "extractive"
            )

    def test_validate_compression_request_invalid_strategy(self):
        """Test compression request validation with invalid strategy."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            RequestValidator.validate_compression_request(
                "Hello world", 50, "starcoder", "invalid"
            )

    def test_validate_compression_request_preview_strategy(self):
        """Test compression request validation with preview strategy."""
        # Preview strategy should bypass strategy validation
        RequestValidator.validate_compression_request(
            "Hello world", 50, "starcoder", "preview"
        )
