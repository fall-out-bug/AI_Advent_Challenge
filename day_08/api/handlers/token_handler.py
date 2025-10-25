"""
Token Service Handler - FastAPI handler for token service.

This module contains the HTTP handling layer for the token service,
separated from business logic concerns.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio

from services.token_service import (
    TokenService,
    TokenCountRequest,
    TokenCountResponse,
    CompressionRequest,
    CompressionResponse,
    BatchTokenCountRequest,
    BatchTokenCountResponse
)
from core.validators.request_validator import RequestValidator
from utils.logging import LoggerFactory


# Pydantic models for API
class TokenCountRequestModel(BaseModel):
    """Pydantic model for token count request."""
    text: str = Field(..., min_length=1, description="Text to count tokens for")
    model_name: str = Field(default="starcoder", description="Model name for token counting")


class TokenCountResponseModel(BaseModel):
    """Pydantic model for token count response."""
    count: int = Field(..., description="Number of tokens")
    model_name: str = Field(..., description="Model name used")
    estimated_cost: float = Field(default=0.0, description="Estimated cost in tokens")


class CompressionRequestModel(BaseModel):
    """Pydantic model for compression request."""
    text: str = Field(..., min_length=1, description="Text to compress")
    max_tokens: int = Field(..., gt=0, description="Maximum number of tokens")
    model_name: str = Field(default="starcoder", description="Model name for token counting")
    strategy: str = Field(..., description="Compression strategy to use")


class CompressionResponseModel(BaseModel):
    """Pydantic model for compression response."""
    original_text: str = Field(..., description="Original text")
    compressed_text: str = Field(..., description="Compressed text")
    original_tokens: int = Field(..., description="Original token count")
    compressed_tokens: int = Field(..., description="Compressed token count")
    compression_ratio: float = Field(..., description="Compression ratio")
    strategy_used: str = Field(..., description="Strategy used for compression")


class BatchTokenCountRequestModel(BaseModel):
    """Pydantic model for batch token count request."""
    texts: List[str] = Field(..., min_length=1, description="List of texts to count tokens for")
    model_name: str = Field(default="starcoder", description="Model name for token counting")


class BatchTokenCountResponseModel(BaseModel):
    """Pydantic model for batch token count response."""
    results: List[TokenCountResponseModel] = Field(..., description="Results for each text")


class TokenServiceHandler:
    """
    FastAPI handler for token service operations.
    
    This handler manages HTTP requests and responses, validation,
    and error handling for the token service.
    """
    
    def __init__(self, service: Optional[TokenService] = None):
        """
        Initialize the token service handler.
        
        Args:
            service: Optional token service instance.
                    If None, creates a new TokenService.
        """
        self.logger = LoggerFactory.create_logger(__name__)
        self.service = service or TokenService()
        self.validator = RequestValidator()
        
        self.logger.info("TokenServiceHandler initialized successfully")
    
    def create_app(self) -> FastAPI:
        """
        Create and configure FastAPI application.
        
        Returns:
            Configured FastAPI application
        """
        app = FastAPI(
            title="Token Analysis Service",
            description="Service for accurate token counting and advanced text compression",
            version="1.0.0"
        )
        
        # Health check endpoint
        @app.get("/health")
        async def health():
            """Health check endpoint."""
            return await self._handle_health_check()
        
        # Token counting endpoints
        @app.post("/count-tokens", response_model=TokenCountResponseModel)
        async def count_tokens(request: TokenCountRequestModel):
            """Count tokens in text using accurate HuggingFace tokenizers."""
            return await self._handle_count_tokens(request)
        
        @app.post("/count-tokens-batch", response_model=BatchTokenCountResponseModel)
        async def count_tokens_batch(request: BatchTokenCountRequestModel):
            """Count tokens for multiple texts in batch."""
            return await self._handle_count_tokens_batch(request)
        
        # Compression endpoints
        @app.post("/compress-text", response_model=CompressionResponseModel)
        async def compress_text(request: CompressionRequestModel):
            """Compress text using specified strategy."""
            return await self._handle_compress_text(request)
        
        @app.post("/preview-compression")
        async def preview_compression(request: CompressionRequestModel):
            """Get preview of compression results for all available strategies."""
            return await self._handle_preview_compression(request)
        
        # Information endpoints
        @app.get("/available-models")
        async def get_available_models():
            """Get list of available models for token counting."""
            return await self._handle_get_available_models()
        
        @app.get("/available-strategies")
        async def get_available_strategies():
            """Get list of available compression strategies."""
            return await self._handle_get_available_strategies()
        
        return app
    
    async def _handle_health_check(self) -> Dict[str, Any]:
        """
        Handle health check request.
        
        Returns:
            Health status information
        """
        try:
            models = self.service.get_available_models()
            return {
                "status": "healthy",
                "service": "token-analysis",
                "available_models": models
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise HTTPException(status_code=500, detail="Service unhealthy")
    
    async def _handle_count_tokens(self, request: TokenCountRequestModel) -> TokenCountResponseModel:
        """
        Handle token counting request.
        
        Args:
            request: Token count request
            
        Returns:
            Token count response
            
        Raises:
            HTTPException: If request processing fails
        """
        try:
            # Validate request
            self.validator.validate_token_count_request(request.text, request.model_name)
            
            # Convert to service request
            service_request = TokenCountRequest(
                text=request.text,
                model_name=request.model_name
            )
            
            # Process request
            service_response = await self.service.count_tokens(service_request)
            
            # Convert to API response
            return TokenCountResponseModel(
                count=service_response.count,
                model_name=service_response.model_name,
                estimated_cost=service_response.estimated_cost
            )
            
        except ValueError as e:
            self.logger.warning(f"Invalid token count request: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            self.logger.error(f"Token counting failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _handle_count_tokens_batch(self, request: BatchTokenCountRequestModel) -> BatchTokenCountResponseModel:
        """
        Handle batch token counting request.
        
        Args:
            request: Batch token count request
            
        Returns:
            Batch token count response
            
        Raises:
            HTTPException: If request processing fails
        """
        try:
            # Validate request
            self.validator.validate_batch_token_count_request(request.texts, request.model_name)
            
            # Convert to service request
            service_request = BatchTokenCountRequest(
                texts=request.texts,
                model_name=request.model_name
            )
            
            # Process request
            service_response = await self.service.batch_count_tokens(service_request)
            
            # Convert to API response
            response_models = [
                TokenCountResponseModel(
                    count=result.count,
                    model_name=result.model_name,
                    estimated_cost=result.estimated_cost
                )
                for result in service_response.results
            ]
            
            return BatchTokenCountResponseModel(results=response_models)
            
        except ValueError as e:
            self.logger.warning(f"Invalid batch token count request: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            self.logger.error(f"Batch token counting failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _handle_compress_text(self, request: CompressionRequestModel) -> CompressionResponseModel:
        """
        Handle text compression request.
        
        Args:
            request: Compression request
            
        Returns:
            Compression response
            
        Raises:
            HTTPException: If request processing fails
        """
        try:
            # Validate request
            self.validator.validate_compression_request(
                request.text, 
                request.max_tokens, 
                request.model_name, 
                request.strategy
            )
            
            # Convert to service request
            service_request = CompressionRequest(
                text=request.text,
                max_tokens=request.max_tokens,
                model_name=request.model_name,
                strategy=request.strategy
            )
            
            # Process request
            service_response = await self.service.compress_text(service_request)
            
            # Convert to API response
            return CompressionResponseModel(
                original_text=service_response.original_text,
                compressed_text=service_response.compressed_text,
                original_tokens=service_response.original_tokens,
                compressed_tokens=service_response.compressed_tokens,
                compression_ratio=service_response.compression_ratio,
                strategy_used=service_response.strategy_used
            )
            
        except ValueError as e:
            self.logger.warning(f"Invalid compression request: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            self.logger.error(f"Text compression failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _handle_preview_compression(self, request: CompressionRequestModel) -> Dict[str, Any]:
        """
        Handle compression preview request.
        
        Args:
            request: Compression request
            
        Returns:
            Compression preview results
            
        Raises:
            HTTPException: If request processing fails
        """
        try:
            # Validate request
            self.validator.validate_compression_request(
                request.text, 
                request.max_tokens, 
                request.model_name, 
                "preview"  # Strategy validation bypassed for preview
            )
            
            # Convert to service request
            service_request = CompressionRequest(
                text=request.text,
                max_tokens=request.max_tokens,
                model_name=request.model_name,
                strategy=request.strategy
            )
            
            # Process request
            return await self.service.preview_compression(service_request)
            
        except ValueError as e:
            self.logger.warning(f"Invalid compression preview request: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            self.logger.error(f"Compression preview failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _handle_get_available_models(self) -> Dict[str, List[str]]:
        """
        Handle get available models request.
        
        Returns:
            Available models information
        """
        try:
            models = self.service.get_available_models()
            return {"models": models}
        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _handle_get_available_strategies(self) -> Dict[str, Any]:
        """
        Handle get available strategies request.
        
        Returns:
            Available strategies information
        """
        try:
            return self.service.get_available_strategies()
        except Exception as e:
            self.logger.error(f"Failed to get available strategies: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
