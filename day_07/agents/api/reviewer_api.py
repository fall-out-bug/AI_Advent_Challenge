"""FastAPI service for code reviewer agent."""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from agents.core.code_reviewer import CodeReviewerAgent
from communication.message_schema import (
    AgentHealthResponse,
    AgentStatsResponse,
    CodeReviewRequest,
    CodeReviewResponse,
)

# Global agent instance
reviewer_agent: CodeReviewerAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global reviewer_agent

    # Startup
    model_name = os.getenv("MODEL_NAME", "starcoder")
    reviewer_agent = CodeReviewerAgent(model_name=model_name)

    # Check model availability
    is_available = await reviewer_agent.model_client.check_availability()
    if is_available:
        print(f"✅ {model_name} model is available")
    else:
        print(f"⚠️  Warning: {model_name} model may not be available")

    # Wait for model to be available
    print(f"Waiting for {model_name} to be available...")
    max_retries = 30
    for attempt in range(max_retries):
        try:
            # Test model connection
            await reviewer_agent._call_model(
                prompt="Test connection", max_tokens=10
            )
            print(f"{model_name} is available!")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(
                    f"{model_name} not ready, retrying in 2 seconds... "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(2)
            else:
                print(
                    f"Failed to connect to {model_name} after {max_retries} attempts: {e}"
                )
                raise RuntimeError(f"{model_name} service unavailable")

    yield

    # Shutdown
    print("Shutting down reviewer agent...")


app = FastAPI(
    title="Code Reviewer Agent",
    description="AI agent for reviewing and analyzing Python code",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest) -> CodeReviewResponse:
    """Review Python code and tests for quality and best practices.

    Args:
        request: Code review request

    Returns:
        Code review results

    Raises:
        HTTPException: If review fails
    """
    try:
        if not reviewer_agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        result = await reviewer_agent.process(request)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code review failed: {str(e)}")


@app.get("/health", response_model=AgentHealthResponse)
async def health_check() -> AgentHealthResponse:
    """Check agent health status.

    Returns:
        Health status information
    """
    if not reviewer_agent:
        return AgentHealthResponse(
            status="unhealthy", agent_type="reviewer", uptime=0.0
        )

    return AgentHealthResponse(
        status="healthy", agent_type="reviewer", uptime=reviewer_agent.get_uptime()
    )


@app.get("/stats", response_model=AgentStatsResponse)
async def get_stats() -> AgentStatsResponse:
    """Get agent statistics.

    Returns:
        Agent performance statistics
    """
    if not reviewer_agent:
        return AgentStatsResponse(
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            average_response_time=0.0,
            total_tokens_used=0,
        )

    stats = reviewer_agent.stats
    return AgentStatsResponse(
        total_requests=stats["total_requests"],
        successful_requests=stats["successful_requests"],
        failed_requests=stats["failed_requests"],
        average_response_time=reviewer_agent.get_average_response_time(),
        total_tokens_used=stats["total_tokens_used"],
    )


@app.post("/analyze-pep8")
async def analyze_pep8(request: Dict[str, str]) -> Dict[str, Any]:
    """Analyze PEP8 compliance of code.

    Args:
        request: Dictionary with 'code' key

    Returns:
        PEP8 analysis results

    Raises:
        HTTPException: If analysis fails
    """
    try:
        if not reviewer_agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        code = request.get("code", "")

        if not code:
            raise HTTPException(status_code=400, detail="Code is required")

        analysis = await reviewer_agent.analyze_pep8_compliance(code)

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PEP8 analysis failed: {str(e)}")


@app.post("/analyze-test-coverage")
async def analyze_test_coverage(request: Dict[str, str]) -> Dict[str, Any]:
    """Analyze test coverage.

    Args:
        request: Dictionary with 'function_code' and 'test_code' keys

    Returns:
        Test coverage analysis

    Raises:
        HTTPException: If analysis fails
    """
    try:
        if not reviewer_agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        function_code = request.get("function_code", "")
        test_code = request.get("test_code", "")

        if not function_code:
            raise HTTPException(status_code=400, detail="Function code is required")

        if not test_code:
            raise HTTPException(status_code=400, detail="Test code is required")

        analysis = await reviewer_agent.analyze_test_coverage(function_code, test_code)

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Test coverage analysis failed: {str(e)}"
        )


@app.post("/calculate-complexity")
async def calculate_complexity(request: Dict[str, str]) -> Dict[str, float]:
    """Calculate code complexity score.

    Args:
        request: Dictionary with 'code' key

    Returns:
        Complexity score

    Raises:
        HTTPException: If calculation fails
    """
    try:
        if not reviewer_agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        code = request.get("code", "")

        if not code:
            raise HTTPException(status_code=400, detail="Code is required")

        complexity_score = reviewer_agent.calculate_complexity_score(code)

        return {"complexity_score": complexity_score}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Complexity calculation failed: {str(e)}"
        )


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
    port = int(os.getenv("PORT", 9002))
    uvicorn.run(
        "reviewer_api:app", host="0.0.0.0", port=port, reload=False, log_level="info"
    )
