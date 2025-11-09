"""Parallel agent orchestrator for concurrent execution.

Following Clean Architecture and the Zen of Python:
- Simple is better than complex
- Readability counts
- There should be one obvious way to do it
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class ParallelOrchestrator:
    """Orchestrator for executing multiple agents concurrently.

    Provides parallel agent execution using asyncio.gather() with:
    - Concurrent agent execution
    - Result aggregation
    - Graceful error handling
    - Timeout management
    - Partial failure support
    """

    def __init__(self):
        """Initialize parallel orchestrator."""
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "partial_failures": 0,
        }

    async def execute_parallel(
        self,
        tasks: List[Tuple[Any, Any]],
        timeout: Optional[float] = None,
        fail_fast: bool = False,
    ) -> List[Any]:
        """Execute multiple agents in parallel.

        Args:
            tasks: List of (agent, request) tuples to execute
            timeout: Optional timeout in seconds
            fail_fast: If True, stop on first failure

        Returns:
            List of results (or None for failed tasks)

        Raises:
            TimeoutError: If execution exceeds timeout
        """
        self.stats["total_executions"] += 1
        start_time = datetime.now()

        logger.info(f"Starting parallel execution of {len(tasks)} tasks")

        # Create coroutines for all tasks
        coroutines = [
            self._execute_single_task(agent, request) for agent, request in tasks
        ]

        try:
            # Execute with optional timeout
            if timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*coroutines, return_exceptions=not fail_fast),
                    timeout=timeout,
                )
            else:
                results = await asyncio.gather(
                    *coroutines, return_exceptions=not fail_fast
                )

            # Analyze results
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful

            self.stats["successful_executions"] += successful
            self.stats["failed_executions"] += failed

            if successful > 0 and failed > 0:
                self.stats["partial_failures"] += 1

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Parallel execution completed in {elapsed:.2f}s "
                f"({successful} successful, {failed} failed)"
            )

            return results

        except asyncio.TimeoutError:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Parallel execution timed out after {elapsed:.2f}s")
            self.stats["failed_executions"] += 1
            raise
        except Exception as e:
            # Handle non-timeout exceptions when fail_fast=True
            elapsed = (datetime.now() - start_time).total_seconds()
            error_msg = (
                f"Parallel execution failed after {elapsed:.2f}s: "
                f"{type(e).__name__}: {str(e)}"
            )
            logger.error(error_msg)
            self.stats["failed_executions"] += 1
            raise

    async def _execute_single_task(self, agent: Any, request: Any) -> Any:
        """Execute a single agent task.

        Args:
            agent: Agent to execute
            request: Request to pass to agent

        Returns:
            Agent result

        Raises:
            Exception: If agent execution fails
        """
        try:
            logger.debug(f"Executing {agent.__class__.__name__}")
            result = await agent.process(request)
            return result
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            raise

    async def execute_with_aggregation(
        self,
        tasks: List[Tuple[Any, Any]],
        aggregation_strategy: str = "all",
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute parallel tasks and aggregate results.

        Args:
            tasks: List of (agent, request) tuples
            aggregation_strategy: How to aggregate results
                - "all": Return all results
                - "first": Return first successful result
                - "majority": Return majority of results
            timeout: Optional timeout in seconds

        Returns:
            Aggregated results dictionary
        """
        results = await self.execute_parallel(tasks, timeout=timeout)

        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]

        if aggregation_strategy == "all":
            return {
                "results": successful_results,
                "failed_count": len(failed_results),
                "total_count": len(results),
            }
        elif aggregation_strategy == "first":
            return {
                "result": successful_results[0] if successful_results else None,
                "failed_count": len(failed_results),
            }
        elif aggregation_strategy == "majority":
            threshold = len(tasks) // 2 + 1
            return {
                "results": successful_results[:threshold],
                "failed_count": len(failed_results),
                "meets_threshold": len(successful_results) >= threshold,
            }
        else:
            return {"results": results}

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics.

        Returns:
            Statistics dictionary
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset orchestrator statistics."""
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "partial_failures": 0,
        }
