"""Multi-agent orchestrator for coordinating code generation and review.

Following Clean Architecture and the Zen of Python:
- Simple is better than complex
- Readability counts
- There should be one obvious way to do it
"""

import logging
from datetime import datetime
from typing import Optional

from src.domain.agents.code_generator import CodeGeneratorAgent
from src.domain.agents.code_reviewer import CodeReviewerAgent
from src.domain.messaging.message_schema import (
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
    """Orchestrator for coordinating multi-agent workflow."""

    def __init__(
        self,
        generator_agent: Optional[CodeGeneratorAgent] = None,
        reviewer_agent: Optional[CodeReviewerAgent] = None,
    ):
        """Initialize the orchestrator.

        Args:
            generator_agent: Code generator agent (created if None)
            reviewer_agent: Code reviewer agent (created if None)
        """
        self.generator = generator_agent or CodeGeneratorAgent()
        self.reviewer = reviewer_agent or CodeReviewerAgent()

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
            # Execute workflow steps
            generation_result = await self._generate_code_step(request)
            review_result = await self._review_code_step(request, generation_result)

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
        self, request: OrchestratorRequest
    ) -> CodeGenerationResponse:
        """Execute the code generation step.

        Args:
            request: Orchestrator request

        Returns:
            Code generation result

        Raises:
            Exception: If generation fails
        """
        generation_request = CodeGenerationRequest(
            task_description=request.task_description,
            language=request.language,
            requirements=request.requirements,
            model_name=request.model_name,
        )

        logger.info("Generating code...")
        result = await self.generator.process(generation_request)

        return result

    async def _review_code_step(
        self,
        request: OrchestratorRequest,
        generation_result: CodeGenerationResponse,
    ) -> CodeReviewResponse:
        """Execute the code review step.

        Args:
            request: Orchestrator request
            generation_result: Result from code generation

        Returns:
            Code review result

        Raises:
            Exception: If review fails
        """
        # Review uses model from request

        review_request = CodeReviewRequest(
            task_description=request.task_description,
            generated_code=generation_result.generated_code,
            tests=generation_result.tests,
            metadata=generation_result.metadata,
        )

        logger.info("Reviewing code...")
        result = await self.reviewer.process(review_request)

        return result

    async def _finalize_workflow(
        self,
        request: OrchestratorRequest,
        generation_result: Optional[CodeGenerationResponse],
        review_result: Optional[CodeReviewResponse],
        workflow_time: float,
        success: bool,
        error_message: Optional[str] = None,
    ) -> OrchestratorResponse:
        """Finalize workflow and create response.

        Args:
            request: Orchestrator request
            generation_result: Generation result
            review_result: Review result
            workflow_time: Total workflow time
            success: Whether workflow succeeded
            error_message: Error message if failed

        Returns:
            Orchestrator response
        """
        if success:
            self.stats["successful_workflows"] += 1
        else:
            self.stats["failed_workflows"] += 1

        # Update average workflow time
        self._update_average_workflow_time(workflow_time)

        return OrchestratorResponse(
            task_description=request.task_description,
            success=success,
            generation_result=generation_result,
            review_result=review_result,
            workflow_time=workflow_time,
            error_message=error_message,
        )

    def _update_average_workflow_time(self, new_time: float) -> None:
        """Update average workflow time.

        Args:
            new_time: New workflow time
        """
        total_workflows = self.stats["total_workflows"]
        current_avg = self.stats["average_workflow_time"]

        if total_workflows == 1:
            self.stats["average_workflow_time"] = new_time
        else:
            # Calculate running average
            self.stats["average_workflow_time"] = (
                current_avg * (total_workflows - 1) + new_time
            ) / total_workflows

    def get_stats(self) -> dict:
        """Get orchestrator statistics.

        Returns:
            Statistics dictionary
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset orchestrator statistics."""
        self.stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_workflow_time": 0.0,
        }
