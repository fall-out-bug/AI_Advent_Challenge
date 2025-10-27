"""Experiment API routes.

Note: Legacy adapter routes have been removed in Phase 2.
Use the new Phase 2 API endpoints instead.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional


class RunExperimentRequest(BaseModel):
    """Request model for running experiment."""

    experiment_name: str
    model_name: str
    session_id: Optional[str] = None


def create_experiment_router() -> APIRouter:
    """
    Create experiment API router.

    Returns:
        Configured API router
    """
    router = APIRouter(prefix="/api/experiments", tags=["experiments"])

    @router.post("/run")
    async def run_experiment(request: RunExperimentRequest):
        """
        Run experiment using Phase 2 architecture.

        Args:
            request: Experiment request

        Returns:
            Experiment results
        """
        raise HTTPException(
            status_code=501,
            detail="Legacy adapter-based experiments are deprecated. "
            "Please use the new Phase 2 API endpoints.",
        )

    @router.get("/status")
    async def get_status():
        """
        Get status of experiment endpoints.

        Returns:
            Status information
        """
        return {
            "status": "deprecated",
            "message": "Legacy adapter-based experiments are deprecated. "
            "Please use the new Phase 2 API endpoints.",
        }

    return router
