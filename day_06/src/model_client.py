"""
Client for working with local language models.

Provides unified interface for interacting with various
local models through HTTP API.
Following Python Zen principles: "Explicit is better than implicit".
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import httpx

from .base_client import BaseModelClient, ModelResponse, ModelClientError, ModelConnectionError, ModelRequestError, ModelTimeoutError
from .constants import MODEL_PORTS, DEFAULT_TIMEOUT, MAX_TOKENS, DEFAULT_TEMPERATURE, TEST_MAX_TOKENS, ModelName


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


class LocalModelClient(BaseModelClient):
    """
    Client for working with local models.
    
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
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def make_request(self, model_name: str, prompt: str) -> ModelResponse:
        """
        Make request to model.
        
        Args:
            model_name: Model name (qwen, mistral, tinyllama)
            prompt: Prompt text
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            ModelConnectionError: If connection fails
            ModelRequestError: If request fails
            ModelTimeoutError: If request times out
        """
        if model_name not in MODEL_PORTS:
            raise ModelRequestError(f"Unknown model: {model_name}")
        
        port = MODEL_PORTS[model_name]
        url = f"http://localhost:{port}/chat"
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_TOKENS,
            "temperature": DEFAULT_TEMPERATURE
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            
            data = response.json()
            
            return ModelResponse(
                response=data["response"],
                response_tokens=data["response_tokens"],
                input_tokens=data["input_tokens"],
                total_tokens=data["total_tokens"],
                model_name=model_name,
                response_time=response_time
            )
            
        except httpx.ConnectError as e:
            raise ModelConnectionError(f"Failed to connect to model {model_name}: {e}")
        except httpx.TimeoutException as e:
            raise ModelTimeoutError(f"Request to model {model_name} timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ModelRequestError(f"HTTP error for model {model_name}: {e}")
        except Exception as e:
            raise ModelClientError(f"Unexpected error with model {model_name}: {e}")
    
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
        
        for model_name in MODEL_PORTS.keys():
            for riddle in riddles:
                try:
                    result = await self.test_riddle(riddle, model_name, verbose)
                    results.append(result)
                except Exception as e:
                    print(f"Error testing {model_name} on riddle: {e}")
                    continue
        
        return results
    
    async def check_availability(self, model_name: str) -> bool:
        """
        Check if specific model is available.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            bool: True if model is available
        """
        if model_name not in MODEL_PORTS:
            return False
        
        try:
            port = MODEL_PORTS[model_name]
            url = f"http://localhost:{port}/chat"
            response = await self.client.post(
                url, 
                json={
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": TEST_MAX_TOKENS
                }
            )
            return response.status_code == 200
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException):
            return False
    
    async def check_model_availability(self) -> Dict[str, bool]:
        """
        Check availability of all models.
        
        Returns:
            Dict[str, bool]: Availability status of each model
        """
        availability = {}
        
        for model_name in MODEL_PORTS.keys():
            availability[model_name] = await self.check_availability(model_name)
        
        return availability
