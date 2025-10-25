"""
Sequential orchestrator for agent coordination.

Following Python Zen: "Simple is better than complex",
"Explicit is better than implicit", and "There should be one obvious way to do it".

This orchestrator executes agents in a sequential order, where each agent
receives the output of the previous agent as input. This is perfect for
workflows like code generation followed by code review.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..agents.schemas import AgentRequest, AgentResponse, TaskMetadata
from .adapters import CommunicationAdapter
from .base_orchestrator import (
    BaseOrchestrator,
    OrchestrationResult,
    OrchestrationStatus,
    OrchestrationConfig
)


class SequentialOrchestrator(BaseOrchestrator):
    """
    Sequential orchestrator for agent workflows.
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    
    This orchestrator executes agents in sequence, where each agent
    receives the output of the previous agent. Perfect for workflows
    like: Generator -> Reviewer -> Formatter.
    """
    
    def __init__(
        self,
        adapter: CommunicationAdapter,
        config: Optional[OrchestrationConfig] = None
    ):
        """
        Initialize sequential orchestrator.
        
        Args:
            adapter: Communication adapter for agent interaction
            config: Orchestration configuration (optional)
        """
        super().__init__(adapter, config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def orchestrate(
        self,
        agents: Dict[str, AgentRequest],
        metadata: Optional[TaskMetadata] = None
    ) -> OrchestrationResult:
        """
        Execute agents in sequential order.
        
        Args:
            agents: Dictionary mapping agent IDs to requests (order matters!)
            metadata: Optional task metadata
            
        Returns:
            OrchestrationResult: Sequential execution result
            
        Raises:
            Exception: If orchestration fails
        """
        start_time = datetime.now().timestamp()
        self.logger.info(f"Starting sequential orchestration with {len(agents)} agents")
        
        # Create result structure
        results = {}
        errors = {}
        current_context = None
        
        try:
            # Execute agents in order
            for i, (agent_id, request) in enumerate(agents.items()):
                if self._cancelled:
                    self.logger.info("Sequential orchestration cancelled")
                    break
                
                self.logger.debug(f"Executing agent {agent_id} (step {i + 1}/{len(agents)})")
                
                try:
                    # Modify request with previous context if available
                    modified_request = self._prepare_request(request, current_context, i)
                    
                    # Execute agent
                    response = await self._execute_agent(agent_id, modified_request)
                    results[agent_id] = response
                    
                    # Update context for next agent
                    current_context = self._extract_context(response, agent_id)
                    
                    self.logger.debug(f"Agent {agent_id} completed, context updated")
                    
                    # Fail fast if configured
                    if self.config.fail_fast and not response.success:
                        self.logger.error(f"Fail fast triggered by agent {agent_id}")
                        break
                    
                except Exception as e:
                    error_msg = f"Agent {agent_id} failed: {str(e)}"
                    errors[agent_id] = error_msg
                    self.logger.error(error_msg)
                    
                    if self.config.fail_fast:
                        self.logger.error("Fail fast triggered by agent failure")
                        break
            
            # Determine final status
            execution_time = datetime.now().timestamp() - start_time
            
            if self._cancelled:
                status = OrchestrationStatus.CANCELLED
            elif errors and not results:
                status = OrchestrationStatus.FAILED
            elif errors:
                status = OrchestrationStatus.COMPLETED  # Partial success
            else:
                status = OrchestrationStatus.COMPLETED
            
            result = OrchestrationResult(
                status=status,
                results=results,
                errors=errors,
                execution_time=execution_time,
                metadata=metadata
            )
            
            self.logger.info(
                f"Sequential orchestration completed: {status.value}, "
                f"{len(results)} successful, {len(errors)} failed, "
                f"{execution_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = datetime.now().timestamp() - start_time
            self.logger.error(f"Sequential orchestration failed: {str(e)}")
            
            return OrchestrationResult(
                status=OrchestrationStatus.FAILED,
                results=results,
                errors={**errors, "orchestrator": str(e)},
                execution_time=execution_time,
                metadata=metadata
            )
    
    def _prepare_request(
        self,
        original_request: AgentRequest,
        previous_context: Optional[Dict[str, Any]],
        step_index: int
    ) -> AgentRequest:
        """
        Prepare request with previous context.
        
        Args:
            original_request: Original agent request
            previous_context: Context from previous agent
            step_index: Current step index
            
        Returns:
            AgentRequest: Modified request with context
        """
        # Create new context combining original and previous
        context = original_request.context or {}
        
        if previous_context:
            # Add previous results to context
            context.update({
                "previous_results": previous_context,
                "step_index": step_index,
                "is_sequential": True
            })
        
        # Create modified request
        return AgentRequest(
            task=original_request.task,
            context=context,
            metadata=original_request.metadata
        )
    
    def _extract_context(
        self,
        response: AgentResponse,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Extract context from agent response.
        
        Args:
            response: Agent response
            agent_id: Agent identifier
            
        Returns:
            Dict[str, Any]: Extracted context
        """
        context = {
            "agent_id": agent_id,
            "result": response.result,
            "success": response.success,
            "timestamp": datetime.now().timestamp()
        }
        
        # Add quality metrics if available
        if response.quality:
            context["quality"] = response.quality.model_dump()
        
        # Add metadata if available
        if response.metadata:
            context["metadata"] = response.metadata.model_dump()
        
        return context
    
    async def orchestrate_with_pipeline(
        self,
        pipeline: List[Dict[str, Any]],
        initial_request: AgentRequest,
        metadata: Optional[TaskMetadata] = None
    ) -> OrchestrationResult:
        """
        Execute predefined pipeline of agents.
        
        Args:
            pipeline: List of agent configurations
            initial_request: Initial request to start pipeline
            metadata: Optional task metadata
            
        Returns:
            OrchestrationResult: Pipeline execution result
            
        Example:
            pipeline = [
                {"agent_id": "generator", "task_modifier": "Generate code for: {task}"},
                {"agent_id": "reviewer", "task_modifier": "Review this code: {result}"}
            ]
        """
        self.logger.info(f"Starting pipeline with {len(pipeline)} steps")
        
        # Build agent requests from pipeline
        agents = {}
        current_request = initial_request
        
        for i, step in enumerate(pipeline):
            agent_id = step["agent_id"]
            task_modifier = step.get("task_modifier", "{task}")
            
            # Apply task modifier
            if "{task}" in task_modifier:
                task = task_modifier.format(task=current_request.task)
            elif "{result}" in task_modifier and i > 0:
                # Get result from previous step
                prev_agent_id = pipeline[i-1]["agent_id"]
                if prev_agent_id in agents:
                    # This is a bit tricky - we'd need the actual result
                    # For now, use a placeholder
                    task = task_modifier.format(result="[PREVIOUS_RESULT]")
                else:
                    task = task_modifier
            else:
                task = task_modifier
            
            # Create request for this step
            request = AgentRequest(
                task=task,
                context=current_request.context,
                metadata=current_request.metadata
            )
            
            agents[agent_id] = request
            current_request = request
        
        return await self.orchestrate(agents, metadata)
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current pipeline execution status.
        
        Returns:
            Dict[str, Any]: Pipeline status information
        """
        return {
            "orchestrator_type": "sequential",
            "is_running": self.is_running(),
            "running_tasks": len(self._running_tasks),
            "cancelled": self._cancelled,
            "config": self.config.model_dump()
        }
