"""
Parallel orchestrator for concurrent agent execution.

Following Python Zen: "Simple is better than complex",
"Explicit is better than implicit", and "There should be one obvious way to do it".

This orchestrator executes multiple agents concurrently, useful for
testing multiple models simultaneously or running independent tasks
in parallel for better performance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from ..agents.schemas import AgentRequest, AgentResponse, TaskMetadata
from .adapters import CommunicationAdapter
from .base_orchestrator import (
    BaseOrchestrator,
    OrchestrationResult,
    OrchestrationStatus,
    OrchestrationConfig
)


class ParallelOrchestrator(BaseOrchestrator):
    """
    Parallel orchestrator for concurrent agent execution.
    
    Following Python Zen: "Simple is better than complex"
    and "Explicit is better than implicit".
    
    This orchestrator executes multiple agents concurrently, which is
    useful for testing multiple models simultaneously or running
    independent tasks in parallel for better performance.
    """
    
    def __init__(
        self,
        adapter: CommunicationAdapter,
        config: Optional[OrchestrationConfig] = None
    ):
        """
        Initialize parallel orchestrator.
        
        Args:
            adapter: Communication adapter for agent interaction
            config: Orchestration configuration (optional)
        """
        super().__init__(adapter, config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
    
    async def orchestrate(
        self,
        agents: Dict[str, AgentRequest],
        metadata: Optional[TaskMetadata] = None
    ) -> OrchestrationResult:
        """
        Execute agents in parallel.
        
        Args:
            agents: Dictionary mapping agent IDs to requests
            metadata: Optional task metadata
            
        Returns:
            OrchestrationResult: Parallel execution result
            
        Raises:
            Exception: If orchestration fails
        """
        start_time = datetime.now().timestamp()
        self.logger.info(f"Starting parallel orchestration with {len(agents)} agents")
        
        # Create tasks for all agents
        tasks = {}
        for agent_id, request in agents.items():
            if self._cancelled:
                break
            
            task = asyncio.create_task(
                self._execute_agent_with_semaphore(agent_id, request)
            )
            tasks[agent_id] = task
            self._running_tasks[agent_id] = task
        
        try:
            # Wait for all tasks to complete
            results = await self._wait_for_completion(tasks)
            
            # Separate successful results from errors
            successful_results = {}
            errors = {}
            
            for agent_id, result in results.items():
                if isinstance(result, Exception):
                    errors[agent_id] = str(result)
                else:
                    successful_results[agent_id] = result
            
            # Determine final status
            execution_time = datetime.now().timestamp() - start_time
            
            if self._cancelled:
                status = OrchestrationStatus.CANCELLED
            elif errors and not successful_results:
                status = OrchestrationStatus.FAILED
            elif errors:
                status = OrchestrationStatus.COMPLETED  # Partial success
            else:
                status = OrchestrationStatus.COMPLETED
            
            result = OrchestrationResult(
                status=status,
                results=successful_results,
                errors=errors,
                execution_time=execution_time,
                metadata=metadata
            )
            
            self.logger.info(
                f"Parallel orchestration completed: {status.value}, "
                f"{len(successful_results)} successful, {len(errors)} failed, "
                f"{execution_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = datetime.now().timestamp() - start_time
            self.logger.error(f"Parallel orchestration failed: {str(e)}")
            
            return OrchestrationResult(
                status=OrchestrationStatus.FAILED,
                results={},
                errors={"orchestrator": str(e)},
                execution_time=execution_time,
                metadata=metadata
            )
        
        finally:
            # Clean up running tasks
            self._running_tasks.clear()
    
    async def _execute_agent_with_semaphore(
        self,
        agent_id: str,
        request: AgentRequest
    ) -> AgentResponse:
        """
        Execute agent with concurrency control.
        
        Args:
            agent_id: Agent identifier
            request: Agent request
            
        Returns:
            AgentResponse: Agent response
            
        Raises:
            Exception: If agent execution fails
        """
        async with self._semaphore:
            if self._cancelled:
                raise Exception("Orchestration cancelled")
            
            return await self._execute_agent(agent_id, request)
    
    async def orchestrate_with_batching(
        self,
        agents: Dict[str, AgentRequest],
        batch_size: Optional[int] = None,
        metadata: Optional[TaskMetadata] = None
    ) -> OrchestrationResult:
        """
        Execute agents in batches for controlled concurrency.
        
        Args:
            agents: Dictionary mapping agent IDs to requests
            batch_size: Size of each batch (defaults to max_concurrent)
            metadata: Optional task metadata
            
        Returns:
            OrchestrationResult: Batched execution result
        """
        batch_size = batch_size or self.config.max_concurrent
        self.logger.info(f"Starting batched orchestration: {len(agents)} agents in batches of {batch_size}")
        
        start_time = datetime.now().timestamp()
        all_results = {}
        all_errors = {}
        
        # Split agents into batches
        agent_items = list(agents.items())
        batches = [
            agent_items[i:i + batch_size]
            for i in range(0, len(agent_items), batch_size)
        ]
        
        try:
            # Process each batch
            for batch_num, batch in enumerate(batches):
                if self._cancelled:
                    self.logger.info("Batched orchestration cancelled")
                    break
                
                self.logger.debug(f"Processing batch {batch_num + 1}/{len(batches)}")
                
                # Execute batch
                batch_agents = dict(batch)
                batch_result = await self.orchestrate(batch_agents, metadata)
                
                # Merge results
                all_results.update(batch_result.results)
                all_errors.update(batch_result.errors)
                
                # Fail fast if configured
                if self.config.fail_fast and batch_result.errors:
                    self.logger.error("Fail fast triggered in batch")
                    break
            
            # Determine final status
            execution_time = datetime.now().timestamp() - start_time
            
            if self._cancelled:
                status = OrchestrationStatus.CANCELLED
            elif all_errors and not all_results:
                status = OrchestrationStatus.FAILED
            elif all_errors:
                status = OrchestrationStatus.COMPLETED  # Partial success
            else:
                status = OrchestrationStatus.COMPLETED
            
            return OrchestrationResult(
                status=status,
                results=all_results,
                errors=all_errors,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except Exception as e:
            execution_time = datetime.now().timestamp() - start_time
            self.logger.error(f"Batched orchestration failed: {str(e)}")
            
            return OrchestrationResult(
                status=OrchestrationStatus.FAILED,
                results=all_results,
                errors={**all_errors, "orchestrator": str(e)},
                execution_time=execution_time,
                metadata=metadata
            )
    
    async def orchestrate_with_race(
        self,
        agents: Dict[str, AgentRequest],
        winner_takes_all: bool = True,
        metadata: Optional[TaskMetadata] = None
    ) -> OrchestrationResult:
        """
        Execute agents in race condition - first successful result wins.
        
        Args:
            agents: Dictionary mapping agent IDs to requests
            winner_takes_all: If True, cancel other agents when one succeeds
            metadata: Optional task metadata
            
        Returns:
            OrchestrationResult: Race execution result
        """
        start_time = datetime.now().timestamp()
        self.logger.info(f"Starting race orchestration with {len(agents)} agents")
        
        # Create tasks for all agents
        tasks = {}
        for agent_id, request in agents.items():
            task = asyncio.create_task(
                self._execute_agent_with_semaphore(agent_id, request)
            )
            tasks[agent_id] = task
        
        try:
            # Wait for first successful completion
            done, pending = await asyncio.wait(
                tasks.values(),
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Find the winner
            winner_agent_id = None
            winner_response = None
            
            for task in done:
                agent_id = self._get_agent_id_for_task(task, tasks)
                try:
                    response = await task
                    if response.success:
                        winner_agent_id = agent_id
                        winner_response = response
                        break
                except Exception:
                    continue
            
            # Cancel remaining tasks if winner found
            if winner_takes_all and winner_agent_id:
                for task in pending:
                    task.cancel()
            
            # Wait for remaining tasks to complete or cancel
            if pending:
                await asyncio.wait(pending, timeout=5.0)
            
            # Build results
            results = {}
            errors = {}
            
            if winner_agent_id and winner_response:
                results[winner_agent_id] = winner_response
                self.logger.info(f"Race won by agent: {winner_agent_id}")
            else:
                # No winner found, collect all errors
                for agent_id, task in tasks.items():
                    try:
                        response = await task
                        if response.success:
                            results[agent_id] = response
                        else:
                            errors[agent_id] = response.error or "Unknown error"
                    except Exception as e:
                        errors[agent_id] = str(e)
            
            execution_time = datetime.now().timestamp() - start_time
            
            status = OrchestrationStatus.COMPLETED if results else OrchestrationStatus.FAILED
            
            return OrchestrationResult(
                status=status,
                results=results,
                errors=errors,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except Exception as e:
            execution_time = datetime.now().timestamp() - start_time
            self.logger.error(f"Race orchestration failed: {str(e)}")
            
            return OrchestrationResult(
                status=OrchestrationStatus.FAILED,
                results={},
                errors={"orchestrator": str(e)},
                execution_time=execution_time,
                metadata=metadata
            )
    
    def get_concurrency_status(self) -> Dict[str, Any]:
        """
        Get current concurrency status.
        
        Returns:
            Dict[str, Any]: Concurrency status information
        """
        return {
            "orchestrator_type": "parallel",
            "is_running": self.is_running(),
            "running_tasks": len(self._running_tasks),
            "max_concurrent": self.config.max_concurrent,
            "semaphore_value": self._semaphore._value,
            "cancelled": self._cancelled,
            "config": self.config.model_dump()
        }
