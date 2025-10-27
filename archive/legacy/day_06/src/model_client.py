"""
Client for working with local language models.

Provides unified interface for interacting with various
local models through HTTP API.
Following Python Zen principles: "Explicit is better than implicit".
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import Dict, List
from dataclasses import dataclass

from shared.clients.unified_client import UnifiedModelClient
from shared.clients.base_client import ModelResponse
from shared.config.models import MODEL_CONFIGS, get_local_models
from shared.config.constants import DEFAULT_TIMEOUT, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, TEST_MAX_TOKENS
from shared.exceptions.model_errors import ModelClientError, ModelConnectionError, ModelRequestError, ModelTimeoutError


@dataclass
class ModelTestResult:
    """Model test result on a riddle."""
    riddle: str
    model_name: str
    direct_answer: str
    stepwise_answer: str
    direct_response_time: float
    stepwise_response_time: float
    direct_tokens: int
    stepwise_tokens: int


class LocalModelClient(UnifiedModelClient):
    """
    Client for working with local models.
    
    This is a wrapper around UnifiedModelClient that provides
    backward compatibility and additional testing functionality.
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    """
    
    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize client.
        
        Args:
            timeout: HTTP client timeout in seconds
        """
        super().__init__(timeout)
    
    async def _make_request(self, model_name: str, prompt: str) -> ModelResponse:
        """
        Backward compatibility wrapper for make_request.
        
        Args:
            model_name: Model name
            prompt: Prompt text
            
        Returns:
            ModelResponse: Model response
        """
        return await self.make_request(model_name, prompt)
    
    async def test_riddle(
        self, 
        riddle: str, 
        model_name: str,
        verbose: bool = False
    ) -> ModelTestResult:
        """
        Test model on riddle in two modes.
        
        Args:
            riddle: Riddle text
            model_name: Model name for testing
            verbose: Whether to output model communication to console
            
        Returns:
            ModelTestResult: Test result
        """
        if verbose:
            print(f"\n🤖 Testing model {model_name}")
            print(f"📝 Riddle: {riddle}")
        
        # Direct answer
        direct_prompt = f"{riddle}\nAnswer:"
        if verbose:
            print(f"\n💬 Direct request to {model_name}...")
        direct_response = await self._make_request(model_name, direct_prompt)
        
        if verbose:
            print(f"✅ Direct answer ({direct_response.response_time:.2f}s):")
            print(f"   {direct_response.response}")
        
        # Stepwise answer
        stepwise_prompt = f"{riddle}\nSolve step by step and explain your reasoning before answering."
        if verbose:
            print(f"\n🧠 Stepwise request to {model_name}...")
        stepwise_response = await self._make_request(model_name, stepwise_prompt)
        
        if verbose:
            print(f"✅ Stepwise answer ({stepwise_response.response_time:.2f}s):")
            print(f"   {stepwise_response.response}")
            print("-" * 60)
        
        return ModelTestResult(
            riddle=riddle,
            model_name=model_name,
            direct_answer=direct_response.response,
            stepwise_answer=stepwise_response.response,
            direct_response_time=direct_response.response_time,
            stepwise_response_time=stepwise_response.response_time,
            direct_tokens=direct_response.response_tokens,
            stepwise_tokens=stepwise_response.response_tokens
        )
    
    async def test_all_models(self, riddles: List[str], verbose: bool = False) -> List[ModelTestResult]:
        """
        Test all models on all riddles.
        
        Args:
            riddles: List of riddles for testing
            verbose: Whether to output model communication to console
            
        Returns:
            List[ModelTestResult]: List of test results
        """
        results = []
        
        for model_name in MODEL_CONFIGS.keys():
            if model_name in ["qwen", "mistral", "tinyllama"]:  # Only local models
                for riddle in riddles:
                    try:
                        result = await self.test_riddle(riddle, model_name, verbose)
                        results.append(result)
                    except Exception as e:
                        print(f"Error testing {model_name} on riddle: {e}")
                        continue
        
        return results
