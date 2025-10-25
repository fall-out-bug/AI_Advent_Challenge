"""
Token Analysis Service - FastAPI service for heavy ML operations.

This service runs in a separate container and provides:
- Accurate token counting with HuggingFace tokenizers
- Advanced text compression strategies
- TF-IDF based summarization
- Semantic chunking
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging

# Import our modules
from core.accurate_token_counter import AccurateTokenCounter
from core.advanced_compressor import SummarizationCompressor, ExtractiveCompressor, SemanticChunker
from models.data_models import TokenInfo, CompressionResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Token Analysis Service",
    description="Service for accurate token counting and advanced text compression",
    version="1.0.0"
)

# Initialize components
token_counter = AccurateTokenCounter()
extractive_compressor = ExtractiveCompressor(token_counter)
semantic_chunker = SemanticChunker(token_counter)

# Pydantic models for API
class TokenCountRequest(BaseModel):
    text: str
    model_name: str = "starcoder"

class TokenCountResponse(BaseModel):
    count: int
    model_name: str
    estimated_cost: float = 0.0

class CompressionRequest(BaseModel):
    text: str
    max_tokens: int
    model_name: str = "starcoder"
    strategy: str

class CompressionResponse(BaseModel):
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    strategy_used: str

class BatchTokenCountRequest(BaseModel):
    texts: List[str]
    model_name: str = "starcoder"

class BatchTokenCountResponse(BaseModel):
    results: List[TokenCountResponse]

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "token-analysis",
        "available_models": token_counter.get_available_models()
    }

@app.post("/count-tokens", response_model=TokenCountResponse)
async def count_tokens(request: TokenCountRequest):
    """
    Count tokens in text using accurate HuggingFace tokenizers.
    
    Args:
        request: TokenCountRequest with text and model_name
        
    Returns:
        TokenCountResponse with token count and metadata
    """
    try:
        token_info = token_counter.count_tokens(request.text, request.model_name)
        
        return TokenCountResponse(
            count=token_info.count,
            model_name=token_info.model_name,
            estimated_cost=token_info.estimated_cost
        )
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/count-tokens-batch", response_model=BatchTokenCountResponse)
async def count_tokens_batch(request: BatchTokenCountRequest):
    """
    Count tokens for multiple texts in batch.
    
    Args:
        request: BatchTokenCountRequest with list of texts
        
    Returns:
        BatchTokenCountResponse with results for each text
    """
    try:
        results = []
        for text in request.texts:
            token_info = token_counter.count_tokens(text, request.model_name)
            results.append(TokenCountResponse(
                count=token_info.count,
                model_name=token_info.model_name,
                estimated_cost=token_info.estimated_cost
            ))
        
        return BatchTokenCountResponse(results=results)
    except Exception as e:
        logger.error(f"Error in batch token counting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compress-text", response_model=CompressionResponse)
async def compress_text(request: CompressionRequest):
    """
    Compress text using specified strategy.
    
    Args:
        request: CompressionRequest with text, max_tokens, model_name, and strategy
        
    Returns:
        CompressionResponse with compression result
    """
    try:
        if request.strategy == "extractive":
            result = extractive_compressor.compress(
                request.text, 
                request.max_tokens, 
                request.model_name
            )
        elif request.strategy == "semantic":
            result = semantic_chunker.compress(
                request.text, 
                request.max_tokens, 
                request.model_name
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported strategy: {request.strategy}. Available: extractive, semantic"
            )
        
        return CompressionResponse(
            original_text=result.original_text,
            compressed_text=result.compressed_text,
            original_tokens=result.original_tokens,
            compressed_tokens=result.compressed_tokens,
            compression_ratio=result.compression_ratio,
            strategy_used=result.strategy_used
        )
    except Exception as e:
        logger.error(f"Error compressing text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/available-models")
async def get_available_models():
    """Get list of available models for token counting."""
    return {
        "models": token_counter.get_available_models()
    }

@app.get("/available-strategies")
async def get_available_strategies():
    """Get list of available compression strategies."""
    return {
        "strategies": ["extractive", "semantic"],
        "descriptions": {
            "extractive": "TF-IDF based extractive summarization",
            "semantic": "Semantic chunking with importance scoring"
        }
    }

@app.post("/preview-compression")
async def preview_compression(request: CompressionRequest):
    """
    Get preview of compression results for all available strategies.
    
    Args:
        request: CompressionRequest with text and max_tokens
        
    Returns:
        Dict with preview results for each strategy
    """
    try:
        results = {}
        
        # Test extractive compression
        try:
            extractive_result = extractive_compressor.compress(
                request.text, 
                request.max_tokens, 
                request.model_name
            )
            results["extractive"] = {
                "compression_ratio": extractive_result.compression_ratio,
                "compressed_tokens": extractive_result.compressed_tokens,
                "preview": extractive_result.compressed_text[:200] + "..." if len(extractive_result.compressed_text) > 200 else extractive_result.compressed_text
            }
        except Exception as e:
            results["extractive"] = {"error": str(e)}
        
        # Test semantic compression
        try:
            semantic_result = semantic_chunker.compress(
                request.text, 
                request.max_tokens, 
                request.model_name
            )
            results["semantic"] = {
                "compression_ratio": semantic_result.compression_ratio,
                "compressed_tokens": semantic_result.compressed_tokens,
                "preview": semantic_result.compressed_text[:200] + "..." if len(semantic_result.compressed_text) > 200 else semantic_result.compressed_text
            }
        except Exception as e:
            results["semantic"] = {"error": str(e)}
        
        return results
    except Exception as e:
        logger.error(f"Error in compression preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
