"""
Base orchestrator for agent coordination patterns.

Following Python Zen: "Simple is better than complex",
"Explicit is better than implicit", and "There should be one obvious way to do it".

This module provides the foundation for orchestrating multiple agents
in various patterns (sequential, parallel, etc.) with proper error handling,
logging, and result tracking.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field

from ..agents.schemas import AgentRequest, AgentResponse, TaskMetadata
from .adapters import CommunicationAdapter, AdapterType, DirectAdapter


class OrchestrationStatus(Enum):
    """Status of orchestration execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestrationResult(BaseModel):
    """
    Result of orchestration execution.
    
    Following Python Zen: "Explicit is better than implicit".
    """
    
    status: OrchestrationStatus = Field(..., description="Execution status")
    results: Dict[str, AgentResponse] = Field(default_factory=dict, description="Agent results by ID")
    errors: Dict[str, str] = Field(default_factory=dict, description="Errors by agent ID")
    execution_time: float = Field(..., description="Total execution time in seconds")
    metadata: Optional[TaskMetadata] = Field(None, description="Task metadata")
    
    @property
    def success(self) -> bool:
        """Check if orchestration was successful."""
        return self.status == OrchestrationStatus.COMPLETED and not self.errors
    
    @property
    def failed_agents(self) -> List[str]:
        """Get list of failed agent IDs."""
        return list(self.errors.keys())


class OrchestrationConfig(BaseModel):
    """
    Configuration for orchestration.
    
    Following Python Zen: "Explicit is better than implicit".
    """
    
    timeout: float = Field(300.0, ge=1.0, le=3600.0, description="Total timeout in seconds")
    max_concurrent: int = Field(10, ge=1, le=100, description="Maximum concurrent agents")
    retry_failed: bool = Field(True, description="Whether to retry failed agents")
    max_retries: int = Field(2, ge=0, le=5, description="Maximum retry attempts")
    fail_fast: bool = Field(False, description="Stop on first failure")


class BaseOrchestrator(ABC):
    """
    Abstract base class for agent orchestration.
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    
    This class provides the foundation for coordinating multiple agents
    in various execution patterns with proper error handling, logging,
    and result tracking.
    """
    
    def __init__(
        self,
        adapter: CommunicationAdapter,
        config: Optional[OrchestrationConfig] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            adapter: Communication adapter for agent interaction
            config: Orchestration configuration (optional)
        """
        self.adapter = adapter
        self.config = config or OrchestrationConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._cancelled = False
    
    @abstractmethod
    async def orchestrate(
        self,
        agents: Dict[str, AgentRequest],
        metadata: Optional[TaskMetadata] = None
    ) -> OrchestrationResult:
        """
        Orchestrate agent execution.
        
        Args:
            agents: Dictionary mapping agent IDs to requests
            metadata: Optional task metadata
            
        Returns:
            OrchestrationResult: Orchestration execution result
            
        Raises:
            Exception: If orchestration fails
        """
        pass
    
    async def _execute_agent(
        self,
        agent_id: str,
        request: AgentRequest,
        attempt: int = 1
    ) -> AgentResponse:
        """
        Execute single agent with retry logic.
        
        Args:
            agent_id: Agent identifier
            request: Agent request
            attempt: Current attempt number
            
        Returns:
            AgentResponse: Agent response
            
        Raises:
            Exception: If agent execution fails after retries
        """
        try:
            self.logger.debug(f"Executing agent {agent_id} (attempt {attempt})")
            
            # Check if agent is available
            if not await self.adapter.is_available(agent_id):
                raise Exception(f"Agent {agent_id} is not available")
            
            # Execute agent
            response = await self.adapter.send_request(agent_id, request)
            
            if not response.success:
                raise Exception(f"Agent {agent_id} failed: {response.error}")
            
            self.logger.debug(f"Agent {agent_id} completed successfully")
            return response
            
        except Exception as e:
            self.logger.warning(f"Agent {agent_id} attempt {attempt} failed: {str(e)}")
            
            # Retry logic
            if (self.config.retry_failed and 
                attempt < self.config.max_retries and 
                not self._cancelled):
                
                await asyncio.sleep(1.0 * attempt)  # Exponential backoff
                return await self._execute_agent(agent_id, request, attempt + 1)
            
            raise
    
    async def _wait_for_completion(
        self,
        tasks: Dict[str, asyncio.Task],
        timeout: Optional[float] = None
    ) -> Dict[str, Union[AgentResponse, Exception]]:
        """
        Wait for task completion with timeout.
        
        Args:
            tasks: Dictionary of agent ID to task mapping
            timeout: Optional timeout override
            
        Returns:
            Dict[str, Union[AgentResponse, Exception]]: Results by agent ID
        """
        timeout = timeout or self.config.timeout
        results = {}
        
        try:
            # Wait for all tasks with timeout
            done, pending = await asyncio.wait(
                tasks.values(),
                timeout=timeout,
                return_when=asyncio.ALL_COMPLETED
            )
            
            # Process completed tasks
            for task in done:
                agent_id = self._get_agent_id_for_task(task, tasks)
                try:
                    results[agent_id] = await task
                except Exception as e:
                    results[agent_id] = e
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                agent_id = self._get_agent_id_for_task(task, tasks)
                results[agent_id] = Exception("Task cancelled due to timeout")
            
        except asyncio.TimeoutError:
            self.logger.error(f"Orchestration timed out after {timeout} seconds")
            # Cancel all remaining tasks
            for task in tasks.values():
                if not task.done():
                    task.cancel()
            
            # Mark remaining as timeout errors
            for agent_id, task in tasks.items():
                if agent_id not in results:
                    results[agent_id] = Exception("Task timed out")
        
        return results
    
    def _get_agent_id_for_task(
        self,
        task: asyncio.Task,
        tasks: Dict[str, asyncio.Task]
    ) -> str:
        """
        Get agent ID for given task.
        
        Args:
            task: Task to find agent ID for
            tasks: Task mapping
            
        Returns:
            str: Agent ID
        """
        for agent_id, t in tasks.items():
            if t is task:
                return agent_id
        raise ValueError("Task not found in mapping")
    
    async def execute(self, request: AgentRequest, agents: List[Any]) -> List[AgentResponse]:
        """
        Execute request with list of agents (for test compatibility).
        
        Args:
            request: Agent request
            agents: List of agent objects
            
        Returns:
            List[AgentResponse]: List of agent responses
        """
        # Register agents with adapter if direct
        if isinstance(self.adapter, DirectAdapter):
            for agent in agents:
                # Use agent_name or agent_id if available
                agent_id = getattr(agent, 'agent_id', getattr(agent, 'agent_name', None))
                if agent_id:
                    self.adapter.register_agent(agent_id, agent)
        
        # Build agents dict
        agents_dict = {}
        for i, agent in enumerate(agents):
            # Use agent_name, agent_id, or generate one
            agent_id = getattr(agent, 'agent_id', getattr(agent, 'agent_name', f"agent_{i}"))
            agents_dict[agent_id] = request
        
        # Execute orchestration
        result = await self.orchestrate(agents_dict)
        
        # Convert to list of responses
        responses = []
        for agent_id in agents_dict.keys():
            if agent_id in result.results:
                responses.append(result.results[agent_id])
            elif agent_id in result.errors:
                # Create error response
                error_response = AgentResponse(
                    result="",
                    success=False,
                    error=result.errors[agent_id],
                    metadata=None
                )
                responses.append(error_response)
        
        return responses
    
    def cancel(self) -> None:
        """Cancel running orchestration."""
        self._cancelled = True
        for task in self._running_tasks.values():
            if not task.done():
                task.cancel()
        self.logger.info("Orchestration cancelled")
    
    def is_running(self) -> bool:
        """Check if orchestration is running."""
        return any(not task.done() for task in self._running_tasks.values())
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all registered agents.
        
        Returns:
            Dict[str, bool]: Health status by agent ID
        """
        health_status = {}
        
        # For direct adapter, check registered agents
        if self.adapter.get_adapter_type() == AdapterType.DIRECT:
            # This would need access to registered agents - simplified for now
            health_status["direct_agents"] = True
        else:
            # For REST adapter, we'd need to know agent IDs
            # This is a simplified implementation
            health_status["rest_agents"] = True
        
        return health_status
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return {
            "adapter_type": self.adapter.get_adapter_type().value,
            "config": self.config.model_dump(),
            "running_tasks": len(self._running_tasks),
            "cancelled": self._cancelled
        }
