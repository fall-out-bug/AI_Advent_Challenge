"""Abstract base agent for all agents."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from ..clients.base_client import ModelResponse
from ..clients.unified_client import UnifiedModelClient
from .schemas import AgentRequest, AgentResponse, TaskMetadata

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(
        self, client: UnifiedModelClient, agent_name: str, max_retries: int = 3
    ):
        """Initialize base agent."""
        self.client = client
        self.agent_name = agent_name
        self.max_retries = max_retries
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
        }

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process agent request with error handling and statistics."""
        self.stats["total_requests"] += 1
        start_time = asyncio.get_event_loop().time()

        try:
            result = await self._process_with_retry(request)
            self.stats["successful_requests"] += 1
            return result
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Agent {self.agent_name} failed: {str(e)}")
            return self._create_error_response(str(e))
        finally:
            elapsed_time = asyncio.get_event_loop().time() - start_time
            self.stats["total_response_time"] += elapsed_time

    async def _process_with_retry(self, request: AgentRequest) -> AgentResponse:
        """Process request with retry logic."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self._process_impl(request)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))

        raise last_error or Exception("Unknown error")

    @abstractmethod
    async def _process_impl(self, request: AgentRequest) -> AgentResponse:
        """Implementation-specific processing logic."""
        pass

    async def _call_model(
        self,
        prompt: str,
        model_name: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ModelResponse:
        """Make request to model client."""
        return await self.client.make_request(
            model_name=model_name,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _create_error_response(self, error_message: str) -> AgentResponse:
        """Create error response."""
        return AgentResponse(
            result="",
            success=False,
            error=error_message,
            metadata=None,
            quality=None,
        )

    def _create_metadata(
        self, task_type: str, model_name: Optional[str] = None
    ) -> TaskMetadata:
        """Create task metadata."""
        return TaskMetadata(
            task_id=f"{self.agent_name}_{datetime.now().timestamp()}",
            task_type=task_type,
            timestamp=datetime.now().timestamp(),
            model_name=model_name,
        )

    def get_stats(self) -> dict:
        """Get agent statistics."""
        avg_response_time = (
            self.stats["total_response_time"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0
            else 0.0
        )

        return {
            **self.stats,
            "average_response_time": avg_response_time,
            "agent_name": self.agent_name,
        }

    def reset_stats(self) -> None:
        """Reset agent statistics."""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
        }
