"""Base agent class with model integration."""

import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from agents.core.smart_model_selector import get_smart_selector, ModelRecommendation
from agents.core.unified_model_adapter import UnifiedModelAdapter
from agents.core.external_api_config import get_config
from communication.message_schema import TaskMetadata
from constants import (
    CODE_BLOCK_PATTERN,
    COMPLEXITY_PATTERN,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEPS_PATTERN,
    JSON_BLOCK_PATTERN,
    LOC_PATTERN,
    PYTEST_PATTERN,
    TEST_PATTERNS,
    TIME_PATTERN,
)

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents with model integration."""

    def __init__(
        self,
        model_name: str = "starcoder",
        agent_type: str = "base",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        external_provider: Optional[str] = None,
    ):
        """Initialize the base agent.

        Args:
            model_name: Name of model to use (starcoder, mistral, qwen, tinyllama)
            agent_type: Type of agent (generator/reviewer)
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation
            external_provider: External API provider name (if using external API)
        """
        self.model_name = model_name
        self.agent_type = agent_type
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.external_provider = external_provider
        
        # Initialize unified model adapter
        self.model_adapter = UnifiedModelAdapter(
            model_name=model_name,
            external_provider=external_provider
        )
        
        self.start_time = datetime.now()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "response_times": [],
        }

    async def _call_model(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Call model with the given prompt through SDK.

        Args:
            prompt: Input prompt
            max_tokens: Override max tokens
            temperature: Override temperature

        Returns:
            Model response

        Raises:
            Exception: If request fails
        """
        start_time = datetime.now()

        try:
            logger.debug(
                f"Calling {self.model_name} model with {max_tokens or self.max_tokens} tokens"
            )

            result = await self.model_adapter.make_request(
                prompt=prompt,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
            )

            # Update stats
            self.stats["total_requests"] += 1
            self.stats["successful_requests"] += 1
            self.stats["total_tokens_used"] += result.get("total_tokens", 0)

            response_time = (datetime.now() - start_time).total_seconds()
            self.stats["response_times"].append(response_time)

            logger.debug(
                f"Model call completed in {response_time:.2f}s, used {result.get('total_tokens', 0)} tokens"
            )

            return result

        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            logger.error(f"Model call failed: {str(e)}")
            raise

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from model response.

        Args:
            response: Raw response from model

        Returns:
            Extracted code
        """
        # Try to extract code from markdown code blocks
        matches = re.findall(CODE_BLOCK_PATTERN, response, re.DOTALL)

        if matches:
            return matches[0].strip()

        # If no code blocks, try to find function definitions
        function_pattern = r"(def\s+\w+.*?)(?=\n\ndef|\n\nclass|\Z)"
        matches = re.findall(function_pattern, response, re.DOTALL)

        if matches:
            return matches[0].strip()

        # Return the whole response if no patterns match
        return response.strip()

    def _extract_tests_from_response(self, response: str) -> str:
        """Extract tests from model response.

        Args:
            response: Raw response from model

        Returns:
            Extracted test code
        """
        # Look for test sections
        for pattern in TEST_PATTERNS:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                return matches[0].strip()

        # Try to find pytest imports and test functions
        matches = re.findall(PYTEST_PATTERN, response, re.DOTALL)

        if matches:
            return matches[0].strip()

        return ""

    def _extract_metadata_from_response(self, response: str) -> TaskMetadata:
        """Extract metadata from model response.

        Args:
            response: Raw response from model

        Returns:
            Extracted metadata
        """
        # Extract complexity
        complexity_match = re.search(COMPLEXITY_PATTERN, response)
        complexity = complexity_match.group(1).lower() if complexity_match else "medium"

        # Extract lines of code
        loc_match = re.search(LOC_PATTERN, response)
        lines_of_code = int(loc_match.group(1)) if loc_match else 0

        # Extract dependencies
        deps_match = re.search(DEPS_PATTERN, response)
        dependencies = []
        if deps_match:
            deps_str = deps_match.group(1)
            dependencies = [
                dep.strip().strip("\"'") for dep in deps_str.split(",") if dep.strip()
            ]

        # Extract estimated time
        time_match = re.search(TIME_PATTERN, response)
        estimated_time = time_match.group(1).strip() if time_match else None

        return TaskMetadata(
            complexity=complexity,
            lines_of_code=lines_of_code,
            estimated_time=estimated_time,
            dependencies=dependencies,
        )

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from model.

        Args:
            response: Raw response from model

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If JSON parsing fails
        """
        # Try to find JSON in the response
        matches = re.findall(JSON_BLOCK_PATTERN, response, re.DOTALL)

        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        # Try to find JSON without code blocks
        json_start = response.find("{")
        json_end = response.rfind("}") + 1

        if json_start != -1 and json_end > json_start:
            try:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        raise ValueError("No valid JSON found in response")

    def get_uptime(self) -> float:
        """Get agent uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return (datetime.now() - self.start_time).total_seconds()

    def get_average_response_time(self) -> float:
        """Get average response time.

        Returns:
            Average response time in seconds
        """
        if not self.stats["response_times"]:
            return 0.0
        return sum(self.stats["response_times"]) / len(self.stats["response_times"])

    async def switch_to_external_provider(self, provider_name: str) -> bool:
        """Switch to external API provider.

        Args:
            provider_name: Name of external provider

        Returns:
            True if switch was successful
        """
        try:
            # Create new adapter with external provider
            new_adapter = UnifiedModelAdapter(
                model_name=self.model_name,
                external_provider=provider_name
            )
            
            # Check if provider is available
            if await new_adapter.check_availability():
                # Close old adapter
                await self.model_adapter.close()
                
                # Switch to new adapter
                self.model_adapter = new_adapter
                self.external_provider = provider_name
                
                logger.info(f"Switched to external provider: {provider_name}")
                return True
            else:
                logger.warning(f"External provider {provider_name} is not available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to switch to external provider {provider_name}: {e}")
            return False

    async def switch_to_local_model(self, model_name: Optional[str] = None) -> bool:
        """Switch to local model.

        Args:
            model_name: Name of local model (if different from current)

        Returns:
            True if switch was successful
        """
        try:
            target_model = model_name or self.model_name
            
            # Create new adapter for local model
            new_adapter = UnifiedModelAdapter(
                model_name=target_model,
                external_provider=None
            )
            
            # Check if local model is available
            if await new_adapter.check_availability():
                # Close old adapter
                await self.model_adapter.close()
                
                # Switch to new adapter
                self.model_adapter = new_adapter
                self.external_provider = None
                if model_name:
                    self.model_name = model_name
                
                logger.info(f"Switched to local model: {target_model}")
                return True
            else:
                logger.warning(f"Local model {target_model} is not available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to switch to local model {target_model}: {e}")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider.

        Returns:
            Provider information
        """
        return self.model_adapter.get_provider_info()

    async def check_provider_availability(self) -> bool:
        """Check if current provider is available.

        Returns:
            True if provider is available
        """
        return await self.model_adapter.check_availability()

    def get_smart_model_recommendation(
        self, 
        task_description: str, 
        language: str = "python",
        prefer_speed: bool = False,
        prefer_quality: bool = False
    ) -> ModelRecommendation:
        """Get smart model recommendation for a task.

        Args:
            task_description: Description of the task
            language: Programming language
            prefer_speed: Prefer faster models
            prefer_quality: Prefer higher quality models

        Returns:
            Model recommendation
        """
        selector = get_smart_selector()
        return selector.recommend_model(
            task_description, language, prefer_speed, prefer_quality
        )

    def get_all_model_recommendations(
        self, 
        task_description: str, 
        language: str = "python"
    ) -> list[ModelRecommendation]:
        """Get recommendations for all available models.

        Args:
            task_description: Description of the task
            language: Programming language

        Returns:
            List of model recommendations sorted by confidence
        """
        selector = get_smart_selector()
        return selector.get_all_recommendations(task_description, language)

    async def switch_to_smart_model(
        self, 
        task_description: str, 
        language: str = "python",
        prefer_speed: bool = False,
        prefer_quality: bool = False
    ) -> bool:
        """Switch to the best model for a specific task.

        Args:
            task_description: Description of the task
            language: Programming language
            prefer_speed: Prefer faster models
            prefer_quality: Prefer higher quality models

        Returns:
            True if switch was successful
        """
        recommendation = self.get_smart_model_recommendation(
            task_description, language, prefer_speed, prefer_quality
        )
        
        logger.info(f"Smart recommendation: {recommendation.reasoning}")
        
        # Try to switch to recommended model
        if recommendation.model.startswith("gpt-") or recommendation.model.startswith("claude-"):
            # This is a ChadGPT model - find the correct provider name
            config_manager = get_config()
            chadgpt_providers = [
                name for name, config in config_manager.providers.items()
                if config.provider_type.value == "chadgpt"
            ]
            if chadgpt_providers:
                provider_name = chadgpt_providers[0]  # Use first available ChadGPT provider
                return await self.switch_to_external_provider(provider_name)
            else:
                logger.warning("No ChadGPT provider found in configuration")
                return False
        else:
            # This is a local model
            return await self.switch_to_local_model(recommendation.model)

    def get_model_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all available models.

        Returns:
            Dict with model capabilities
        """
        selector = get_smart_selector()
        return {
            model: selector.get_model_info(model) 
            for model in selector.model_capabilities.keys()
        }

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Process a request. Must be implemented by subclasses.

        Returns:
            Processing result
        """
        pass
