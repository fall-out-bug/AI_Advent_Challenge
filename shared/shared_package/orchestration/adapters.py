"""
Communication adapters for flexible agent communication.

Following Python Zen: "Simple is better than complex",
"Explicit is better than implicit", and "There should be one obvious way to do it".

This module implements the Adapter pattern to support both direct async calls
and REST API communication for agents.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

import aiohttp
from pydantic import BaseModel, Field

from ..agents.schemas import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)


class AdapterType(Enum):
    """Adapter types for agent communication."""

    DIRECT = "direct"
    REST = "rest"


class AdapterConfig(BaseModel):
    """
    Configuration for communication adapters.

    Following Python Zen: "Explicit is better than implicit".
    """

    adapter_type: AdapterType = Field(..., description="Type of adapter")
    timeout: float = Field(
        30.0, ge=0.1, le=300.0, description="Request timeout in seconds"
    )
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(
        1.0, ge=0.1, le=10.0, description="Delay between retries"
    )


class CommunicationAdapter(ABC):
    """
    Abstract base class for communication adapters.

    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".

    This class defines the interface that all communication adapters
    must implement, providing a consistent way to communicate with agents
    regardless of the underlying communication mechanism.
    """

    def __init__(self, config: AdapterConfig):
        """
        Initialize communication adapter.

        Args:
            config: Adapter configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def send_request(self, agent_id: str, request: AgentRequest) -> AgentResponse:
        """
        Send request to agent.

        Args:
            agent_id: Identifier for the target agent
            request: Agent request

        Returns:
            AgentResponse: Agent response

        Raises:
            Exception: If communication fails
        """
        pass

    @abstractmethod
    async def is_available(self, agent_id: str) -> bool:
        """
        Check if agent is available.

        Args:
            agent_id: Agent identifier

        Returns:
            bool: True if agent is available
        """
        pass

    @abstractmethod
    def get_adapter_type(self) -> AdapterType:
        """
        Get adapter type.

        Returns:
            AdapterType: Type of this adapter
        """
        pass


class DirectAdapter(CommunicationAdapter):
    """
    Direct adapter for in-process agent communication.

    Following Python Zen: "Simple is better than complex"
    and "There should be one obvious way to do it".

    This adapter communicates directly with agents running in the same process,
    using Python async calls. This is the most efficient communication method
    for agents that are part of the same application.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        """
        Initialize direct adapter.

        Args:
            config: Adapter configuration (optional)
        """
        if config is None:
            config = AdapterConfig(adapter_type=AdapterType.DIRECT)
        super().__init__(config)
        self._agents: Dict[str, Any] = {}

    def register_agent(self, agent_id: str, agent_instance: Any) -> None:
        """
        Register agent instance for direct communication.

        Args:
            agent_id: Agent identifier
            agent_instance: Agent instance
        """
        self._agents[agent_id] = agent_instance
        self.logger.info(f"Registered agent: {agent_id}")

    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister agent instance.

        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")

    async def send_request(self, agent_id: str, request: AgentRequest) -> AgentResponse:
        """
        Send request directly to agent.

        Args:
            agent_id: Agent identifier
            request: Agent request

        Returns:
            AgentResponse: Agent response

        Raises:
            ValueError: If agent is not registered
            Exception: If agent processing fails
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not registered")

        agent = self._agents[agent_id]

        try:
            # Direct async call to agent's process method
            response = await agent.process(request)
            self.logger.debug(f"Direct request to {agent_id} completed")
            return response
        except Exception as e:
            self.logger.error(f"Direct request to {agent_id} failed: {str(e)}")
            raise

    async def is_available(self, agent_id: str) -> bool:
        """
        Check if agent is registered and available.

        Args:
            agent_id: Agent identifier

        Returns:
            bool: True if agent is available
        """
        return agent_id in self._agents

    @property
    def adapter_type(self) -> str:
        """Get adapter type as string."""
        return AdapterType.DIRECT.value

    def get_adapter_type(self) -> AdapterType:
        """
        Get adapter type.

        Returns:
            AdapterType: DIRECT
        """
        return AdapterType.DIRECT


class RestAdapter(CommunicationAdapter):
    """
    REST adapter for distributed agent communication.

    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".

    This adapter communicates with agents via HTTP REST API calls,
    enabling distributed agent architectures where agents run
    in separate processes or on different machines.
    """

    def __init__(self, base_url: str, config: Optional[AdapterConfig] = None):
        """
        Initialize REST adapter.

        Args:
            base_url: Base URL for agent API
            config: Adapter configuration (optional)
        """
        if config is None:
            config = AdapterConfig(adapter_type=AdapterType.REST)
        super().__init__(config)
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP session.

        Returns:
            aiohttp.ClientSession: HTTP session
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def send_request(self, agent_id: str, request: AgentRequest) -> AgentResponse:
        """
        Send request to agent via REST API.

        Args:
            agent_id: Agent identifier
            request: Agent request

        Returns:
            AgentResponse: Agent response

        Raises:
            Exception: If HTTP request fails
        """
        session = await self._get_session()
        url = f"{self.base_url}/agents/{agent_id}/process"

        # Convert request to dict for JSON serialization
        request_data = request.model_dump()

        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                async with session.post(url, json=request_data) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        agent_response = AgentResponse(**response_data)
                        self.logger.debug(f"REST request to {agent_id} completed")
                        return agent_response
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")

            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"REST request attempt {attempt + 1} failed: {str(e)}"
                )

                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)

        self.logger.error(
            f"REST request to {agent_id} failed after {self.config.max_retries} attempts"
        )
        raise last_error or Exception("Unknown REST communication error")

    async def is_available(self, agent_id: str) -> bool:
        """
        Check if agent is available via health check.

        Args:
            agent_id: Agent identifier

        Returns:
            bool: True if agent is available
        """
        session = await self._get_session()
        url = f"{self.base_url}/agents/{agent_id}/health"

        try:
            async with session.get(url) as response:
                return response.status == 200
        except Exception as e:
            self.logger.debug(f"Health check for {agent_id} failed: {str(e)}")
            return False

    @property
    def adapter_type(self) -> str:
        """Get adapter type as string."""
        return AdapterType.REST.value

    def get_adapter_type(self) -> AdapterType:
        """
        Get adapter type.

        Returns:
            AdapterType: REST
        """
        return AdapterType.REST


class AdapterFactory:
    """
    Factory for creating communication adapters.

    Following Python Zen: "Simple is better than complex"
    and "There should be one obvious way to do it".

    This factory provides a clean way to create and configure
    communication adapters based on requirements.
    """

    @staticmethod
    def create_direct_adapter(config: Optional[AdapterConfig] = None) -> DirectAdapter:
        """
        Create direct adapter.

        Args:
            config: Adapter configuration (optional)

        Returns:
            DirectAdapter: Direct communication adapter
        """
        return DirectAdapter(config)

    @staticmethod
    def create_rest_adapter(
        base_url: str, config: Optional[AdapterConfig] = None
    ) -> RestAdapter:
        """
        Create REST adapter.

        Args:
            base_url: Base URL for agent API
            config: Adapter configuration (optional)

        Returns:
            RestAdapter: REST communication adapter
        """
        return RestAdapter(base_url, config)

    @staticmethod
    def create_adapter(adapter_type: AdapterType, **kwargs) -> CommunicationAdapter:
        """
        Create adapter by type.

        Args:
            adapter_type: Type of adapter to create
            **kwargs: Additional arguments for adapter creation

        Returns:
            CommunicationAdapter: Created adapter

        Raises:
            ValueError: If adapter type is not supported
        """
        if adapter_type == AdapterType.DIRECT:
            return AdapterFactory.create_direct_adapter(kwargs.get("config"))
        elif adapter_type == AdapterType.REST:
            base_url = kwargs.get("base_url")
            if not base_url:
                raise ValueError("base_url is required for REST adapter")
            return AdapterFactory.create_rest_adapter(base_url, kwargs.get("config"))
        else:
            raise ValueError(f"Unsupported adapter type: {adapter_type}")
