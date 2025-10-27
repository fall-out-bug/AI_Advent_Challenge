"""Base agent class with model integration.

Following the Zen of Python:
- Simple is better than complex
- Readability counts
- Explicit is better than implicit
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)


# Constants for code extraction patterns
CODE_BLOCK_PATTERN = r"```(?:python)?\s*(.*?)```"
FUNCTION_DEF_PATTERN = r"(def\s+\w+.*?)(?=\n\ndef|\n\nclass|\Z)"
TEST_PATTERNS = [
    r"### TESTS\s*```(?:python)?\s*(.*?)```",
    r"TESTS:\s*```(?:python)?\s*(.*?)```",
    r"```python\s*(import pytest.*?)```",
]
PYTEST_PATTERN = r"(import pytest.*?)(?=\n\n###|\Z)"
JSON_BLOCK_PATTERN = r"```json\s*(.*?)```"

# Metadata extraction patterns
COMPLEXITY_PATTERN = r"Complexity:\s*(\w+)"
LOC_PATTERN = r"Lines of Code:\s*(\d+)"
DEPS_PATTERN = r"Dependencies:\s*\[(.*?)\]"
TIME_PATTERN = r"Estimated Time:\s*([^\n]+)"

# Default configuration
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.7


class TaskMetadata:
    """Metadata about a task.

    Simple data class following the Zen of Python principle:
    "Simple is better than complex"
    """

    def __init__(
        self,
        complexity: str = "medium",
        lines_of_code: int = 0,
        estimated_time: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
    ):
        """Initialize task metadata.

        Args:
            complexity: Complexity level (low/medium/high)
            lines_of_code: Number of lines
            estimated_time: Estimated execution time
            dependencies: Required dependencies
        """
        self.complexity = complexity
        self.lines_of_code = lines_of_code
        self.estimated_time = estimated_time
        self.dependencies = dependencies or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "complexity": self.complexity,
            "lines_of_code": self.lines_of_code,
            "estimated_time": self.estimated_time,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskMetadata":
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            TaskMetadata instance
        """
        return cls(
            complexity=data.get("complexity", "medium"),
            lines_of_code=data.get("lines_of_code", 0),
            estimated_time=data.get("estimated_time"),
            dependencies=data.get("dependencies", []),
        )


class BaseAgent(ABC):
    """Base class for all agents with model integration.

    Following Clean Architecture and the Zen of Python:
    - Beautiful is better than ugly
    - Simple is better than complex
    - Readability counts
    """

    def __init__(
        self,
        model_name: str = "starcoder",
        agent_type: str = "base",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        model_client: Optional[Any] = None,
    ):
        """Initialize the base agent.

        Args:
            model_name: Name of model to use
            agent_type: Type of agent (generator/reviewer)
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation
            model_client: Model client for making requests
        """
        self.model_name = model_name
        self.agent_type = agent_type
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model_client = model_client

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
        """Call model with the given prompt.

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
            logger.debug(f"Calling {self.model_name} model")

            # Call the model client
            result = await self._make_model_request(
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

            logger.debug(f"Model call completed in {response_time:.2f}s")

            return result

        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            logger.error(f"Model call failed: {str(e)}")
            raise

    async def _make_model_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        """Make model request - abstract to be implemented by subclasses.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens
            temperature: Temperature

        Returns:
            Model response

        Raises:
            NotImplementedError: If not implemented
        """
        if self.model_client is None:
            raise NotImplementedError("Model client not provided")

        return await self.model_client.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

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
        matches = re.findall(FUNCTION_DEF_PATTERN, response, re.DOTALL)

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

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Process a request. Must be implemented by subclasses.

        Returns:
            Processing result
        """
        pass
