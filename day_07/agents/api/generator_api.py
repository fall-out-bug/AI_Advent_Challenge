"""FastAPI service for code generator agent."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents.core.code_generator import CodeGeneratorAgent
from communication.message_schema import (
    AgentHealthResponse,
    AgentStatsResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
    RefineRequest,
    RefineResponse,
    ValidateRequest,
    ValidateResponse,
)
from constants import (
    GENERIC_ERROR_MESSAGE,
    HF_TOKEN_ENV_VAR,
    MAX_STARTUP_RETRIES,
    RETRY_DELAY_SECONDS,
)
from exceptions import CodeGenerationError, ConfigurationError, ValidationError

# Configure logging
logger = logging.getLogger(__name__)

# Global agent instance
generator_agent: CodeGeneratorAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global generator_agent

    # Startup
    model_name = os.getenv("MODEL_NAME", "starcoder")

    # Validate required environment variables
    hf_token = os.getenv(HF_TOKEN_ENV_VAR)
    if not hf_token:
        logger.warning(f"{HF_TOKEN_ENV_VAR} environment variable is not set. Using local model without token.")

    generator_agent = CodeGeneratorAgent(model_name=model_name)

    # Check model availability
    is_available = await generator_agent.model_client.check_availability()
    if is_available:
        logger.info(f"✅ {model_name} model is available")
    else:
        logger.warning(f"⚠️  Warning: {model_name} model may not be available")

    # Wait for model to be available
    logger.info(f"Waiting for {model_name} to be available...")
    for attempt in range(MAX_STARTUP_RETRIES):
        try:
            # Test model connection
            await generator_agent._call_model(
                prompt="Test connection", max_tokens=10
            )
            logger.info(f"{model_name} is available!")
            break
        except Exception as e:
            if attempt < MAX_STARTUP_RETRIES - 1:
                logger.warning(
                    f"{model_name} not ready, retrying in {RETRY_DELAY_SECONDS} "
                    f"seconds... (attempt {attempt + 1}/{MAX_STARTUP_RETRIES})"
                )
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            else:
                logger.error(
                    f"Failed to connect to {model_name} after {MAX_STARTUP_RETRIES} attempts: {e}"
                )
                raise ConfigurationError(f"{model_name} service unavailable")

    yield

    # Shutdown
    logger.info("Shutting down generator agent...")


app = FastAPI(
    title="Code Generator Agent",
    description="AI agent for generating Python code and tests",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest) -> CodeGenerationResponse:
    """Generate Python code and tests based on task description.

    Args:
        request: Code generation request

    Returns:
        Generated code and tests

    Raises:
        HTTPException: If generation fails
    """
    try:
        if not generator_agent:
            logger.error("Agent not initialized")
            raise HTTPException(status_code=503, detail="Agent not initialized")

        logger.info(f"Processing code generation request: {request.task_description}")
        result = await generator_agent.process(request)
        logger.info("Code generation completed successfully")
        return result

    except Exception as e:
        logger.error(f"Code generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


@app.get("/health", response_model=AgentHealthResponse)
async def health_check() -> AgentHealthResponse:
    """Check agent health status.

    Returns:
        Health status information
    """
    if not generator_agent:
        return AgentHealthResponse(
            status="unhealthy", agent_type="generator", uptime=0.0
        )

    return AgentHealthResponse(
        status="healthy", agent_type="generator", uptime=generator_agent.get_uptime()
    )


@app.get("/stats", response_model=AgentStatsResponse)
async def get_stats() -> AgentStatsResponse:
    """Get agent statistics.

    Returns:
        Agent performance statistics
    """
    if not generator_agent:
        return AgentStatsResponse(
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            average_response_time=0.0,
            total_tokens_used=0,
        )

    stats = generator_agent.stats
    return AgentStatsResponse(
        total_requests=stats["total_requests"],
        successful_requests=stats["successful_requests"],
        failed_requests=stats["failed_requests"],
        average_response_time=generator_agent.get_average_response_time(),
        total_tokens_used=stats["total_tokens_used"],
    )


@app.post("/refine", response_model=RefineResponse)
async def refine_code(request: RefineRequest) -> RefineResponse:
    """Refine existing code based on feedback.

    Args:
        request: Refine request with code and feedback

    Returns:
        Refined code

    Raises:
        HTTPException: If refinement fails
    """
    try:
        if not generator_agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        refined_code = await generator_agent.refine_code(request.code, request.feedback)

        return RefineResponse(refined_code=refined_code)

    except CodeGenerationError:
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)
    except Exception:
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)


@app.post("/validate", response_model=ValidateResponse)
async def validate_code(request: ValidateRequest) -> ValidateResponse:
    """Validate generated code for basic issues.

    Args:
        request: Validate request with code

    Returns:
        Validation results

    Raises:
        HTTPException: If validation fails
    """
    try:
        if not generator_agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        issues = generator_agent.validate_generated_code(request.code)

        return ValidateResponse(
            valid=len(issues) == 0, issues=issues, issue_count=len(issues)
        )

    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid input provided")
    except Exception:
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler.

    Args:
        request: HTTP request
        exc: Exception that occurred

    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__,
        },
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 9001))
    uvicorn.run(
        "generator_api:app", host="0.0.0.0", port=port, reload=False, log_level="info"
    )
