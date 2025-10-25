"""
Model Switcher Orchestrator for coordinating model switching and workflow.

This module provides the ModelSwitcherOrchestrator class that manages
model availability checking, seamless switching, and statistics tracking
for the model switching demo.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from core.ml_client import TokenAnalysisClient
from models.data_models import ModelWorkflowResult
from utils.logging import LoggerFactory

# Import UnifiedModelClient for model availability checking
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))
from shared_package.clients.unified_client import UnifiedModelClient

# Import SDK orchestration patterns
from shared_package.orchestration.sequential import SequentialOrchestrator
from shared_package.orchestration.adapters import DirectAdapter
from shared_package.agents.code_generator import CodeGeneratorAgent
from shared_package.agents.code_reviewer import CodeReviewerAgent
from shared_package.agents.schemas import AgentRequest, TaskMetadata

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class ModelSwitcherOrchestrator:
    """
    Orchestrator for coordinating model switching and workflow execution.
    
    Manages model availability, switching, and statistics tracking for
    comprehensive model testing and comparison.
    
    Attributes:
        models: List of model names to manage
        current_model: Currently active model
        model_client: TokenAnalysisClient for model interactions
        statistics: Per-model statistics tracking
        logger: Logger instance for structured logging
        
    Example:
        ```python
        from core.model_switcher import ModelSwitcherOrchestrator
        
        # Initialize orchestrator
        orchestrator = ModelSwitcherOrchestrator(models=["starcoder", "mistral"])
        
        # Check availability and switch
        if await orchestrator.check_model_availability("starcoder"):
            await orchestrator.switch_to_model("starcoder")
            
        # Run workflow
        result = await orchestrator.run_workflow_with_model("starcoder", tasks)
        
        # Get statistics
        stats = orchestrator.get_model_statistics()
        ```
    """
    
    def __init__(self, models: List[str], model_client: Optional[TokenAnalysisClient] = None):
        """
        Initialize the model switcher orchestrator.
        
        Args:
            models: List of model names to manage
            model_client: Optional TokenAnalysisClient instance
            
        Example:
            ```python
            orchestrator = ModelSwitcherOrchestrator(
                models=["starcoder", "mistral", "qwen"]
            )
            ```
        """
        self.models = models
        self.current_model: Optional[str] = None
        self.model_client = model_client or TokenAnalysisClient()
        self.unified_client = UnifiedModelClient()  # For model availability checking
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Initialize Docker container management
        self._initialize_docker_management()
        
        # Initialize SDK orchestration if available
        self._initialize_sdk_orchestration()
        
        # Initialize statistics tracking
        self.statistics: Dict[str, Dict[str, Any]] = {}
        for model in models:
            self.statistics[model] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens_used": 0,
                "total_response_time": 0.0,
                "average_response_time": 0.0,
                "last_used": None,
                "availability_checks": 0,
                "successful_switches": 0,
                "failed_switches": 0,
            }
        
        self.logger.info(f"Initialized ModelSwitcherOrchestrator with models: {models}")
    
    def _initialize_docker_management(self) -> None:
        """
        Initialize Docker container management with graceful error handling.
        
        Sets up docker_manager and use_container_management flags based on
        availability of Docker client and ModelDockerManager.
        """
        try:
            from utils.docker_manager import ModelDockerManager
            self.docker_manager = ModelDockerManager()
            self.use_container_management = True
            self.running_containers: Set[str] = set()
            self.logger.info("Docker container management enabled")
        except ImportError as e:
            self.docker_manager = None
            self.use_container_management = False
            self.running_containers: Set[str] = set()
            self.logger.warning(f"Docker management disabled: {e}")
        except Exception as e:
            self.docker_manager = None
            self.use_container_management = False
            self.running_containers: Set[str] = set()
            self.logger.warning(f"Docker client unavailable: {e}")
    
    async def _poll_model_health(
        self, 
        model_name: str, 
        max_attempts: int = 30,
        poll_interval: float = 2.0,
        timeout: float = 60.0
    ) -> bool:
        """
        Poll model health endpoint until ready or timeout.
        
        Args:
            model_name: Name of the model to check
            max_attempts: Maximum number of polling attempts
            poll_interval: Seconds between polls
            timeout: Total timeout in seconds
            
        Returns:
            True if model becomes healthy, False if timeout
            
        Example:
            ```python
            is_healthy = await orchestrator._poll_model_health("starcoder")
            if is_healthy:
                print("Model is ready")
            ```
        """
        start_time = asyncio.get_event_loop().time()
        
        for attempt in range(1, max_attempts + 1):
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                self.logger.error(f"Health check timeout for {model_name} after {elapsed:.1f}s")
                return False
            
            try:
                is_available = await self.unified_client.check_availability(model_name)
                if is_available:
                    self.logger.info(f"{model_name} is healthy after {elapsed:.1f}s ({attempt} attempts)")
                    return True
            except Exception as e:
                self.logger.debug(f"Health check attempt {attempt} failed: {e}")
            
            await asyncio.sleep(poll_interval)
        
        return False
    
    async def _start_container_with_retry(
        self,
        model_name: str,
        max_retries: int = 3,
        base_delay: float = 2.0
    ) -> bool:
        """
        Start container with exponential backoff retry.
        
        Args:
            model_name: Name of the model
            max_retries: Maximum retry attempts
            base_delay: Base delay for exponential backoff
            
        Returns:
            True if container started successfully
            
        Example:
            ```python
            success = await orchestrator._start_container_with_retry("starcoder")
            if success:
                print("Container started successfully")
            ```
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Starting {model_name} container (attempt {attempt + 1}/{max_retries})")
                
                # Start the container
                success = await self.docker_manager.start_model(model_name, wait_time=5)
                if not success:
                    raise Exception(f"Failed to start {model_name} container")
                
                # Poll health endpoint until ready
                is_healthy = await self._poll_model_health(model_name)
                if is_healthy:
                    self.running_containers.add(model_name)
                    return True
                else:
                    self.logger.warning(f"{model_name} container started but health check failed")
                    # Stop unhealthy container
                    await self.docker_manager.stop_model(model_name)
                    
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed to start {model_name}: {e}")
            
            # Exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                self.logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        return False
    
    async def check_model_availability(self, model_name: str) -> bool:
        """
        Check if a model is available, starting container if needed.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model is available, False otherwise
            
        Example:
            ```python
            is_available = await orchestrator.check_model_availability("starcoder")
            if is_available:
                print("StarCoder is ready to use")
            ```
        """
        try:
            self.statistics[model_name]["availability_checks"] += 1
            
            # First check if container management is available
            if self.use_container_management and self.docker_manager:
                # Check if container is already running
                running_models = self.docker_manager.get_running_models()
                
                if model_name in running_models:
                    self.logger.info(f"{model_name} container already running")
                    self.running_containers.add(model_name)
                else:
                    # Container not running, start it with retry
                    self.logger.info(f"{model_name} container not running, starting...")
                    success = await self._start_container_with_retry(model_name)
                    if not success:
                        self.logger.error(f"Failed to start {model_name} after retries")
                        return False
            
            # Verify model is responding via API
            is_available = await self.unified_client.check_availability(model_name)
            
            if is_available:
                self.logger.info(f"Model {model_name} is available and responding")
            else:
                self.logger.warning(f"Model {model_name} container running but not responding")
                
            return is_available
            
        except Exception as e:
            self.logger.error(f"Error checking availability for {model_name}: {e}")
            return False
    
    async def switch_to_model(self, model_name: str) -> bool:
        """
        Switch to the specified model, managing containers sequentially.
        
        Stops current model container before starting the new one to save resources.
        
        Args:
            model_name: Name of the model to switch to
            
        Returns:
            True if switch was successful, False otherwise
            
        Example:
            ```python
            success = await orchestrator.switch_to_model("mistral")
            if success:
                print("Successfully switched to Mistral")
            ```
        """
        try:
            # Stop current model container if container management is enabled
            if self.use_container_management and self.docker_manager and self.current_model:
                if self.current_model != model_name and self.current_model in self.running_containers:
                    self.logger.info(f"Stopping previous model: {self.current_model}")
                    stop_success = await self.docker_manager.stop_model(self.current_model, timeout=30)
                    if stop_success:
                        self.running_containers.discard(self.current_model)
                        self.logger.info(f"Successfully stopped {self.current_model}")
                    else:
                        self.logger.warning(f"Failed to stop {self.current_model}, continuing anyway")
            
            # Check if new model is available (will start container if needed)
            if not await self.check_model_availability(model_name):
                self.statistics[model_name]["failed_switches"] += 1
                self.logger.error(f"Cannot switch to {model_name}: model not available")
                return False
            
            # Update current model
            previous_model = self.current_model
            self.current_model = model_name
            
            # Update statistics
            self.statistics[model_name]["successful_switches"] += 1
            self.statistics[model_name]["last_used"] = datetime.now()
            
            self.logger.info(f"Successfully switched from {previous_model} to {model_name}")
            return True
            
        except Exception as e:
            self.statistics[model_name]["failed_switches"] += 1
            self.logger.error(f"Failed to switch to {model_name}: {e}")
            return False
    
    async def run_workflow_with_model(
        self, 
        model_name: str, 
        tasks: List[Any],
        auto_switch: bool = True
    ) -> ModelWorkflowResult:
        """
        Run a workflow with the specified model.
        
        Args:
            model_name: Name of the model to use
            tasks: List of tasks to execute
            auto_switch: Whether to automatically switch to the model
            
        Returns:
            ModelWorkflowResult containing workflow results and statistics
            
        Example:
            ```python
            tasks = [task1, task2, task3]
            result = await orchestrator.run_workflow_with_model("starcoder", tasks)
            print(f"Workflow completed in {result.total_time:.2f}s")
            ```
        """
        workflow_start = datetime.now()
        
        try:
            # Switch to model if requested
            if auto_switch:
                if not await self.switch_to_model(model_name):
                    raise Exception(f"Failed to switch to model {model_name}")
            
            # Execute tasks
            task_results = []
            for i, task in enumerate(tasks):
                self.logger.info(f"Executing task {i+1}/{len(tasks)} with {model_name}")
                
                try:
                    # Update request statistics
                    self.statistics[model_name]["total_requests"] += 1
                    
                    # Execute task (assuming task has an execute method)
                    if hasattr(task, 'execute'):
                        task_result = await task.execute(self.model_client, model_name)
                    else:
                        # Fallback for simple tasks
                        task_result = await self._execute_simple_task(task, model_name)
                    
                    task_results.append(task_result)
                    self.statistics[model_name]["successful_requests"] += 1
                    
                    # Update token usage if available
                    if hasattr(task_result, 'tokens_used'):
                        self.statistics[model_name]["total_tokens_used"] += task_result.tokens_used
                    
                    # Update response time if available
                    if hasattr(task_result, 'response_time'):
                        self.statistics[model_name]["total_response_time"] += task_result.response_time
                        
                except Exception as e:
                    self.statistics[model_name]["failed_requests"] += 1
                    self.logger.error(f"Task {i+1} failed: {e}")
                    task_results.append({"error": str(e), "success": False})
            
            # Calculate workflow statistics
            workflow_time = (datetime.now() - workflow_start).total_seconds()
            successful_tasks = sum(1 for result in task_results if result.get("success", True))
            
            # Update average response time
            if self.statistics[model_name]["successful_requests"] > 0:
                self.statistics[model_name]["average_response_time"] = (
                    self.statistics[model_name]["total_response_time"] / 
                    self.statistics[model_name]["successful_requests"]
                )
            
            return ModelWorkflowResult(
                model_name=model_name,
                tasks_executed=len(tasks),
                successful_tasks=successful_tasks,
                failed_tasks=len(tasks) - successful_tasks,
                total_time=workflow_time,
                task_results=task_results,
                model_statistics=self.statistics[model_name].copy()
            )
            
        except Exception as e:
            workflow_time = (datetime.now() - workflow_start).total_seconds()
            self.logger.error(f"Workflow failed after {workflow_time:.2f}s: {e}")
            
            return ModelWorkflowResult(
                model_name=model_name,
                tasks_executed=len(tasks),
                successful_tasks=0,
                failed_tasks=len(tasks),
                total_time=workflow_time,
                task_results=[],
                model_statistics=self.statistics[model_name].copy(),
                error_message=str(e)
            )
    
    async def _execute_simple_task(self, task: Any, model_name: str) -> Dict[str, Any]:
        """
        Execute a simple task with the model.
        
        Args:
            task: Task to execute
            model_name: Name of the model to use
            
        Returns:
            Task execution result
        """
        try:
            # For simple string tasks, make a basic request
            if isinstance(task, str):
                response = await self.model_client.make_request(
                    model_name=model_name,
                    prompt=task,
                    max_tokens=500,
                    temperature=0.7
                )
                
                return {
                    "success": True,
                    "response": response.response,
                    "tokens_used": response.total_tokens,
                    "response_time": response.response_time
                }
            else:
                # For other task types, return a placeholder
                return {
                    "success": True,
                    "message": f"Task executed with {model_name}",
                    "task_type": type(task).__name__
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_model_statistics(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a specific model or all models.
        
        Args:
            model_name: Optional specific model name, if None returns all models
            
        Returns:
            Dictionary containing model statistics
            
        Example:
            ```python
            # Get statistics for all models
            all_stats = orchestrator.get_model_statistics()
            
            # Get statistics for specific model
            starcoder_stats = orchestrator.get_model_statistics("starcoder")
            ```
        """
        if model_name:
            if model_name not in self.statistics:
                raise ValueError(f"Model {model_name} not found")
            return self.statistics[model_name].copy()
        else:
            return {model: stats.copy() for model, stats in self.statistics.items()}
    
    def get_current_model(self) -> Optional[str]:
        """
        Get the currently active model.
        
        Returns:
            Name of the current model, or None if no model is active
        """
        return self.current_model
    
    def get_available_models(self) -> List[str]:
        """
        Get list of all configured models.
        
        Returns:
            List of model names
        """
        return self.models.copy()
    
    async def check_all_models_availability(self, start_containers: bool = False) -> Dict[str, bool]:
        """
        Check availability of all configured models.
        
        Args:
            start_containers: Whether to start containers if not running (default: False)
        
        Returns:
            Dictionary mapping model names to availability status
            
        Example:
            ```python
            availability = await orchestrator.check_all_models_availability()
            for model, is_available in availability.items():
                print(f"{model}: {'Available' if is_available else 'Not available'}")
            ```
        """
        availability = {}
        
        for model in self.models:
            if start_containers:
                # Use check_model_availability which will start containers if needed
                availability[model] = await self.check_model_availability(model)
            else:
                # Only check if containers are already running
                if self.use_container_management and self.docker_manager:
                    running_models = self.docker_manager.get_running_models()
                    is_running = model in running_models
                    
                    if is_running:
                        # Verify model is responding via API
                        is_available = await self.unified_client.check_availability(model)
                        availability[model] = is_available
                    else:
                        availability[model] = False
                else:
                    # No container management, just check API
                    availability[model] = await self.unified_client.check_availability(model)
        
        return availability
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all model statistics.
        
        Returns:
            Summary statistics for all models
            
        Example:
            ```python
            summary = orchestrator.get_model_summary()
            print(f"Total requests across all models: {summary['total_requests']}")
            ```
        """
        total_requests = sum(stats["total_requests"] for stats in self.statistics.values())
        total_successful = sum(stats["successful_requests"] for stats in self.statistics.values())
        total_failed = sum(stats["failed_requests"] for stats in self.statistics.values())
        total_tokens = sum(stats["total_tokens_used"] for stats in self.statistics.values())
        
        return {
            "total_models": len(self.models),
            "current_model": self.current_model,
            "total_requests": total_requests,
            "total_successful_requests": total_successful,
            "total_failed_requests": total_failed,
            "total_tokens_used": total_tokens,
            "overall_success_rate": total_successful / total_requests if total_requests > 0 else 0,
            "models": self.statistics
        }
    
    async def cleanup_containers(self) -> None:
        """
        Stop all running model containers.
        
        Should be called at the end of the demo to clean up resources.
        
        Example:
            ```python
            await orchestrator.cleanup_containers()
            print("All containers stopped")
            ```
        """
        if not self.use_container_management or not self.docker_manager:
            return
        
        self.logger.info("Cleaning up running containers...")
        
        for model_name in list(self.running_containers):
            try:
                self.logger.info(f"Stopping {model_name}...")
                success = await self.docker_manager.stop_model(model_name, timeout=30)
                if success:
                    self.running_containers.discard(model_name)
                    self.logger.info(f"Successfully stopped {model_name}")
                else:
                    self.logger.warning(f"Failed to stop {model_name}")
            except Exception as e:
                self.logger.error(f"Error stopping {model_name}: {e}")
        
        self.logger.info("Container cleanup completed")
    
    def _initialize_sdk_orchestration(self) -> None:
        """
        Initialize SDK orchestration patterns.
        
        Sets up SDK orchestrator and agents for enhanced workflow management.
        """
        try:
            # Create direct adapter for SDK agents
            self.sdk_adapter = DirectAdapter()
            
            # Initialize SDK agents for each model
            self.sdk_agents: Dict[str, Dict[str, Any]] = {}
            for model_name in self.models:
                # Create UnifiedModelClient for each model
                from shared_package.clients.unified_client import UnifiedModelClient
                client = UnifiedModelClient()
                
                self.sdk_agents[model_name] = {
                    "generator": CodeGeneratorAgent(
                        client=client,
                        model_name=model_name,
                        max_tokens=2000,
                        temperature=0.7
                    ),
                    "reviewer": CodeReviewerAgent(
                        client=client,
                        model_name=model_name,
                        max_tokens=1500,
                        temperature=0.2
                    )
                }
            
            # Initialize sequential orchestrator with adapter
            self.sdk_orchestrator = SequentialOrchestrator(adapter=self.sdk_adapter)
            self.use_sdk_orchestration = True
            
            self.logger.info("SDK orchestration patterns enabled")
                
        except Exception as e:
            self.sdk_adapter = None
            self.sdk_agents = {}
            self.sdk_orchestrator = None
            self.use_sdk_orchestration = False
            self.logger.error(f"SDK orchestration initialization failed: {e}")
            raise
    
    async def run_sdk_workflow(
        self,
        model_name: str,
        task_description: str,
        language: str = "python",
        requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run SDK orchestrated workflow: Generator → Reviewer.
        
        Args:
            model_name: Name of the model to use
            task_description: Description of the coding task
            language: Programming language
            requirements: Additional requirements
            
        Returns:
            Dictionary containing workflow results
            
        Example:
            ```python
            result = await orchestrator.run_sdk_workflow(
                model_name="starcoder",
                task_description="Write a sorting function",
                language="python",
                requirements=["Use quicksort", "Include tests"]
            )
            print(f"Generated code: {result['generated_code']}")
            print(f"Quality score: {result['quality_score']}")
            ```
        """
        if not self.use_sdk_orchestration:
            raise Exception("SDK orchestration not available - initialization failed")
        
        try:
            # Switch to model first
            if not await self.switch_to_model(model_name):
                raise Exception(f"Failed to switch to model {model_name}")
            
            # Get SDK agents for this model
            if model_name not in self.sdk_agents:
                raise Exception(f"No SDK agents configured for {model_name}")
            
            generator_agent = self.sdk_agents[model_name]["generator"]
            reviewer_agent = self.sdk_agents[model_name]["reviewer"]
            
            # Create request for generator
            generator_request = AgentRequest(
                task=task_description,
                context={
                    "language": language,
                    "requirements": requirements or [],
                    "model_name": model_name,
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                metadata=TaskMetadata(
                    task_id=f"workflow_{hash(task_description)}",
                    task_type="code_generation",
                    timestamp=asyncio.get_event_loop().time(),
                    model_name=model_name
                )
            )
            
            # Run sequential workflow: Generator → Reviewer
            workflow_result = await self.sdk_orchestrator.execute_sequential(
                agents=[generator_agent, reviewer_agent],
                initial_request=generator_request,
                context_passing=True
            )
            
            # Extract results
            generator_response = workflow_result.results[0] if workflow_result.results else None
            reviewer_response = workflow_result.results[1] if len(workflow_result.results) > 1 else None
            
            if not generator_response:
                raise Exception("Generator failed to produce results")
            
            # Update statistics
            self.statistics[model_name]["total_requests"] += 1
            self.statistics[model_name]["successful_requests"] += 1
            
            return {
                "success": True,
                "model_name": model_name,
                "generated_code": generator_response.content,
                "tests": generator_response.tests,
                "quality_score": reviewer_response.quality_score if reviewer_response else None,
                "quality_metrics": reviewer_response.metrics if reviewer_response else None,
                "workflow_time": workflow_result.total_time,
                "total_tokens": workflow_result.total_tokens,
                "agent_statistics": {
                    "generator": generator_agent.get_statistics(),
                    "reviewer": reviewer_agent.get_statistics() if reviewer_response else None
                }
            }
            
        except Exception as e:
            self.statistics[model_name]["failed_requests"] += 1
            self.logger.error(f"SDK workflow failed for {model_name}: {e}")
            
            return {
                "success": False,
                "model_name": model_name,
                "error": str(e),
                "generated_code": None,
                "tests": None,
                "quality_score": None,
                "quality_metrics": None,
                "workflow_time": 0.0,
                "total_tokens": 0
            }
