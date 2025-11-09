"""Agent API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.application.use_cases.generate_code import GenerateCodeUseCase
from src.application.use_cases.review_code import ReviewCodeUseCase


class GenerateCodeRequest(BaseModel):
    """Request model for code generation."""

    prompt: str
    agent_name: str
    model_config_id: Optional[str] = None


class ReviewCodeRequest(BaseModel):
    """Request model for code review."""

    code: str
    agent_name: str
    model_config_id: Optional[str] = None


def create_agent_router(
    generate_code_use_case: GenerateCodeUseCase,
    review_code_use_case: ReviewCodeUseCase,
) -> APIRouter:
    """
    Create agent API router.

    Args:
        generate_code_use_case: Code generation use case
        review_code_use_case: Code review use case

    Returns:
        Configured API router
    """
    router = APIRouter(prefix="/api/agents", tags=["agents"])

    @router.post("/generate")
    async def generate_code(request: GenerateCodeRequest):
        """
        Generate code endpoint.

        Args:
            request: Generation request

        Returns:
            Generated code task
        """
        try:
            task = await generate_code_use_case.execute(
                prompt=request.prompt,
                agent_name=request.agent_name,
                model_config_id=request.model_config_id,
            )
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "response": task.response,
                "quality_metrics": (
                    task.quality_metrics.scores if task.quality_metrics else None
                ),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/review")
    async def review_code(request: ReviewCodeRequest):
        """
        Review code endpoint.

        Args:
            request: Review request

        Returns:
            Code review task
        """
        try:
            task = await review_code_use_case.execute(
                code=request.code,
                agent_name=request.agent_name,
                model_config_id=request.model_config_id,
            )
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "response": task.response,
                "quality_metrics": (
                    task.quality_metrics.scores if task.quality_metrics else None
                ),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
