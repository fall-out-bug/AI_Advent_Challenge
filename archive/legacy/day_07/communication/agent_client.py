"""HTTP client for agent-to-agent communication."""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from communication.message_schema import (
    AgentHealthResponse,
    AgentStatsResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
    CodeReviewRequest,
    CodeReviewResponse,
)

# Configure logging
logger = logging.getLogger(__name__)


class AgentClient:
    """HTTP client for communicating with agent services."""

    def __init__(self, timeout: float = 600.0):
        """Initialize the agent client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _make_request(
        self,
        url: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Make HTTP request to agent service with retry logic.

        Args:
            url: Target URL
            method: HTTP method
            data: Request data
            max_retries: Maximum number of retry attempts

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                logger.debug(
                    f"Making {method} request to {url} (attempt {attempt + 1}/{max_retries + 1})"
                )

                if method.upper() == "POST":
                    response = await self._client.post(url, json=data)
                elif method.upper() == "GET":
                    response = await self._client.get(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                logger.debug(f"Request successful on attempt {attempt + 1}")
                return response.json()

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"Request timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.warning(
                    f"HTTP error {e.response.status_code} on attempt {attempt + 1}: {e.response.text}"
                )
                if e.response.status_code >= 500 and attempt < max_retries:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    raise httpx.HTTPError(
                        f"HTTP error {e.response.status_code}: {e.response.text}"
                    )

            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        # If we get here, all retries failed
        logger.error(f"Request failed after {max_retries + 1} attempts")
        raise httpx.HTTPError(
            f"Request failed after {max_retries + 1} attempts: {last_exception}"
        )

    async def generate_code(
        self, generator_url: str, request: CodeGenerationRequest
    ) -> CodeGenerationResponse:
        """Request code generation from generator agent.

        Args:
            generator_url: URL of the generator agent
            request: Code generation request

        Returns:
            Code generation response

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{generator_url}/generate"
        response_data = await self._make_request(url, "POST", request.model_dump())
        return CodeGenerationResponse(**response_data)

    async def review_code(
        self, reviewer_url: str, request: CodeReviewRequest
    ) -> CodeReviewResponse:
        """Request code review from reviewer agent.

        Args:
            reviewer_url: URL of the reviewer agent
            request: Code review request

        Returns:
            Code review response

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{reviewer_url}/review"
        response_data = await self._make_request(url, "POST", request.model_dump())
        return CodeReviewResponse(**response_data)

    async def check_health(self, agent_url: str) -> AgentHealthResponse:
        """Check agent health status.

        Args:
            agent_url: URL of the agent

        Returns:
            Health response

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{agent_url}/health"
        response_data = await self._make_request(url, "GET")
        return AgentHealthResponse(**response_data)

    async def get_stats(self, agent_url: str) -> AgentStatsResponse:
        """Get agent statistics.

        Args:
            agent_url: URL of the agent

        Returns:
            Statistics response

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{agent_url}/stats"
        response_data = await self._make_request(url, "GET")
        return AgentStatsResponse(**response_data)

    async def wait_for_agent(
        self, agent_url: str, max_retries: int = 10, retry_delay: float = 2.0
    ) -> bool:
        """Wait for agent to become available.

        Args:
            agent_url: URL of the agent
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            True if agent is available, False if max retries exceeded
        """
        for attempt in range(max_retries):
            try:
                health = await self.check_health(agent_url)
                if health.status == "healthy":
                    return True
            except httpx.HTTPError:
                pass

            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)

        return False
