"""Dashboard API routes for real-time metrics visualization."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

from src.infrastructure.monitoring.metrics import get_metrics


def create_dashboard_router() -> APIRouter:
    """Create dashboard API router.

    Returns:
        Configured API router
    """
    router = APIRouter(prefix="/dashboard", tags=["dashboard"])

    @router.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Display metrics dashboard.

        Returns:
            HTML dashboard page
        """
        dashboard_path = Path(__file__).parent.parent / "templates" / "dashboard.html"

        with dashboard_path.open("r") as f:
            return f.read()

    @router.get("/data")
    async def get_dashboard_data():
        """Get metrics data for dashboard.

        Returns:
            Current metrics and recent operations
        """
        metrics = get_metrics()
        recent_ops = metrics.get_recent_operations(limit=100)
        metrics_data = metrics.get_metrics()

        return {
            "metrics": metrics_data,
            "recent_operations": recent_ops,
        }

    return router
