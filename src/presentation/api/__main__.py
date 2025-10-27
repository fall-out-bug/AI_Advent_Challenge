"""FastAPI application entry point."""

from fastapi import FastAPI

from src.application.use_cases.generate_code import GenerateCodeUseCase
from src.application.use_cases.review_code import ReviewCodeUseCase
from src.infrastructure.clients.model_client import ModelClient
from src.infrastructure.clients.simple_model_client import SimpleModelClient
from src.infrastructure.config.settings import Settings
from src.infrastructure.repositories.json_agent_repository import (
    JsonAgentRepository,
)
from src.infrastructure.repositories.model_repository import (
    InMemoryModelRepository,
)
from src.presentation.api.agent_routes import create_agent_router
from src.presentation.api.dashboard_routes import create_dashboard_router
from src.presentation.api.experiment_routes import create_experiment_router
from src.presentation.api.health_routes import create_health_router


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="AI Challenge API",
        description="Clean Architecture API for AI Agents",
        version="1.0.0",
    )

    settings = Settings.from_env()
    agent_repo = JsonAgentRepository(settings.get_agent_storage_path())
    model_repo = InMemoryModelRepository()
    model_client: ModelClient = SimpleModelClient()

    generate_code_use_case = GenerateCodeUseCase(
        agent_repository=agent_repo,
        model_repository=model_repo,
        model_client=model_client,
    )

    review_code_use_case = ReviewCodeUseCase(
        agent_repository=agent_repo,
        model_repository=model_repo,
        model_client=model_client,
    )

    agent_router = create_agent_router(
        generate_code_use_case=generate_code_use_case,
        review_code_use_case=review_code_use_case,
    )

    experiment_router = create_experiment_router()
    dashboard_router = create_dashboard_router()
    health_router = create_health_router(settings)

    app.include_router(agent_router)
    app.include_router(experiment_router)
    app.include_router(dashboard_router)
    app.include_router(health_router)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
