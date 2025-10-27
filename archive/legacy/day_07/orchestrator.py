"""Orchestrator for coordinating multi-agent workflow."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from communication.agent_client import AgentClient
from communication.message_schema import (
    CodeGenerationRequest,
    CodeGenerationResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    OrchestratorRequest,
    OrchestratorResponse,
)

# Configure logging
logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Orchestrator for coordinating code generation and review workflow."""

    def __init__(
        self,
        generator_url: str = "http://localhost:9001",
        reviewer_url: str = "http://localhost:9002",
        results_dir: str = "results",
    ):
        """Initialize the orchestrator.

        Args:
            generator_url: URL of the generator agent
            reviewer_url: URL of the reviewer agent
            results_dir: Directory to save results
        """
        self.generator_url = generator_url
        self.reviewer_url = reviewer_url
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

        # Statistics
        self.stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_workflow_time": 0.0,
        }

    async def process_task(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """Process a complete workflow: generate code and review it.

        Args:
            request: Orchestrator request

        Returns:
            Complete workflow results

        Raises:
            Exception: If workflow fails
        """
        workflow_start = datetime.now()
        self.stats["total_workflows"] += 1

        logger.info(f"Starting workflow for task: {request.task_description}")

        try:
            # Determine models to use
            gen_model = request.model_name
            rev_model = request.reviewer_model_name or request.model_name

            logger.info(f"Using {gen_model} for generation, {rev_model} for review")

            # Execute workflow steps
            generation_result = await self._generate_code_step(request, gen_model)
            review_result = await self._review_code_step(
                request, generation_result, rev_model
            )

            # Calculate workflow time and create response
            workflow_time = (datetime.now() - workflow_start).total_seconds()
            response = await self._finalize_workflow(
                request, generation_result, review_result, workflow_time, True
            )

            logger.info(f"Workflow completed successfully in {workflow_time:.2f}s")
            logger.info(f"Code quality score: {review_result.code_quality_score}/10")

            return response

        except Exception as e:
            workflow_time = (datetime.now() - workflow_start).total_seconds()

            logger.error(f"Workflow failed after {workflow_time:.2f}s: {str(e)}")

            return await self._finalize_workflow(
                request, None, None, workflow_time, False, str(e)
            )

    async def _generate_code_step(
        self, request: OrchestratorRequest, model_name: str
    ) -> CodeGenerationResponse:
        """Execute the code generation step.

        Args:
            request: Orchestrator request
            model_name: Model to use for generation

        Returns:
            Code generation result

        Raises:
            Exception: If generation fails
        """
        generation_request = CodeGenerationRequest(
            task_description=request.task_description,
            language=request.language,
            requirements=request.requirements,
            model_name=model_name,
        )

        async with AgentClient() as client:
            logger.info("Waiting for generator agent to be available...")
            await client.wait_for_agent(self.generator_url)

            logger.info("Generating code...")
            return await client.generate_code(self.generator_url, generation_request)

    async def _review_code_step(
        self,
        request: OrchestratorRequest,
        generation_result: CodeGenerationResponse,
        model_name: str,
    ) -> CodeReviewResponse:
        """Execute the code review step.

        Args:
            request: Orchestrator request
            generation_result: Result from code generation
            model_name: Model to use for review

        Returns:
            Code review result

        Raises:
            Exception: If review fails
        """
        review_request = CodeReviewRequest(
            task_description=request.task_description,
            generated_code=generation_result.generated_code,
            tests=generation_result.tests,
            metadata=generation_result.metadata,
        )

        async with AgentClient() as client:
            logger.info("Waiting for reviewer agent to be available...")
            await client.wait_for_agent(self.reviewer_url)

            logger.info("Reviewing generated code...")
            return await client.review_code(self.reviewer_url, review_request)

    async def _finalize_workflow(
        self,
        request: OrchestratorRequest,
        generation_result: Optional[CodeGenerationResponse],
        review_result: Optional[CodeReviewResponse],
        workflow_time: float,
        success: bool,
        error_message: Optional[str] = None,
    ) -> OrchestratorResponse:
        """Finalize the workflow and save results.

        Args:
            request: Original orchestrator request
            generation_result: Code generation result
            review_result: Code review result
            workflow_time: Total workflow time
            success: Whether workflow succeeded
            error_message: Error message if failed

        Returns:
            Final orchestrator response
        """
        response = OrchestratorResponse(
            task_description=request.task_description,
            generation_result=generation_result,
            review_result=review_result,
            workflow_time=workflow_time,
            success=success,
            error_message=error_message,
        )

        if success:
            await self._save_results(response)
            self._update_average_workflow_time(workflow_time)
            self.stats["successful_workflows"] += 1
        else:
            self.stats["failed_workflows"] += 1

        return response

    async def _save_results(self, response: OrchestratorResponse) -> None:
        """Save workflow results to file.

        Args:
            response: Workflow response to save
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_{timestamp}.json"
        filepath = self.results_dir / filename

        # Convert response to dict for JSON serialization
        result_data = {
            "timestamp": timestamp,
            "task_description": response.task_description,
            "workflow_time": response.workflow_time,
            "success": response.success,
            "error_message": response.error_message,
            "generation_result": (
                response.generation_result.model_dump()
                if response.generation_result
                else None
            ),
            "review_result": (
                response.review_result.model_dump() if response.review_result else None
            ),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Results saved to {filepath}")

    def _update_average_workflow_time(self, workflow_time: float) -> None:
        """Update average workflow time.

        Args:
            workflow_time: Time taken for the workflow
        """
        if self.stats["successful_workflows"] == 0:
            # First successful workflow
            self.stats["average_workflow_time"] = workflow_time
        else:
            # Calculate running average
            current_avg = self.stats["average_workflow_time"]
            count = self.stats["successful_workflows"]
            self.stats["average_workflow_time"] = (
                current_avg * count + workflow_time
            ) / (count + 1)

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents.

        Returns:
            Dictionary with agent statuses
        """
        status = {
            "generator": {"status": "unknown", "uptime": 0.0},
            "reviewer": {"status": "unknown", "uptime": 0.0},
        }

        try:
            async with AgentClient() as client:
                # Check generator
                try:
                    gen_health = await client.check_health(self.generator_url)
                    status["generator"] = {
                        "status": gen_health.status,
                        "uptime": gen_health.uptime,
                    }
                except Exception as e:
                    status["generator"]["error"] = str(e)

                # Check reviewer
                try:
                    rev_health = await client.check_health(self.reviewer_url)
                    status["reviewer"] = {
                        "status": rev_health.status,
                        "uptime": rev_health.uptime,
                    }
                except Exception as e:
                    status["reviewer"]["error"] = str(e)

        except Exception as e:
            status["error"] = str(e)

        return status

    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics from all agents.

        Returns:
            Dictionary with agent statistics
        """
        stats = {"generator": None, "reviewer": None, "orchestrator": self.stats}

        try:
            async with AgentClient() as client:
                # Get generator stats
                try:
                    gen_stats = await client.get_stats(self.generator_url)
                    stats["generator"] = gen_stats.model_dump()
                except Exception as e:
                    stats["generator"] = {"error": str(e)}

                # Get reviewer stats
                try:
                    rev_stats = await client.get_stats(self.reviewer_url)
                    stats["reviewer"] = rev_stats.model_dump()
                except Exception as e:
                    stats["reviewer"] = {"error": str(e)}

        except Exception as e:
            stats["error"] = str(e)

        return stats

    def get_results_summary(self) -> Dict[str, Any]:
        """Get summary of saved results.

        Returns:
            Summary of results
        """
        if not self.results_dir.exists():
            return {"message": "No results directory found"}

        result_files = list(self.results_dir.glob("workflow_*.json"))

        if not result_files:
            return {"message": "No workflow results found"}

        # Analyze results
        successful_workflows = 0
        failed_workflows = 0
        total_workflow_time = 0.0
        quality_scores = []

        for file_path in result_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if data.get("success", False):
                    successful_workflows += 1
                    total_workflow_time += data.get("workflow_time", 0)

                    # Extract quality score
                    review_result = data.get("review_result")
                    if review_result and "code_quality_score" in review_result:
                        quality_scores.append(review_result["code_quality_score"])
                else:
                    failed_workflows += 1

            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

        summary = {
            "total_workflows": len(result_files),
            "successful_workflows": successful_workflows,
            "failed_workflows": failed_workflows,
            "success_rate": (
                successful_workflows / len(result_files) if result_files else 0
            ),
            "average_workflow_time": (
                total_workflow_time / successful_workflows
                if successful_workflows > 0
                else 0
            ),
            "average_quality_score": (
                sum(quality_scores) / len(quality_scores) if quality_scores else 0
            ),
            "quality_score_range": {
                "min": min(quality_scores) if quality_scores else 0,
                "max": max(quality_scores) if quality_scores else 0,
            },
        }

        return summary


# Convenience function for simple usage
async def process_simple_task(
    task_description: str,
    language: str = "python",
    requirements: Optional[list] = None,
    generator_url: str = "http://localhost:9001",
    reviewer_url: str = "http://localhost:9002",
) -> OrchestratorResponse:
    """Process a simple task with default settings.

    Args:
        task_description: Description of the task
        language: Programming language
        requirements: Additional requirements
        generator_url: URL of the generator agent
        reviewer_url: URL of the reviewer agent

    Returns:
        Workflow results
    """
    orchestrator = MultiAgentOrchestrator(
        generator_url=generator_url, reviewer_url=reviewer_url
    )

    request = OrchestratorRequest(
        task_description=task_description,
        language=language,
        requirements=requirements or [],
    )

    return await orchestrator.process_task(request)
