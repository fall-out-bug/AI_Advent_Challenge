"""HTTP wrapper for MCP server using FastAPI."""
import asyncio
import os
import sys
from time import perf_counter
from typing import Any, Dict, List
from uuid import uuid4

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import Response
    from pydantic import BaseModel
    from uvicorn import run
except ImportError:
    # Log error before importing logger (logger might not be available)
    sys.stderr.write("ERROR: fastapi and uvicorn required for HTTP mode\n")
    sys.stderr.write("Install with: pip install fastapi uvicorn\n")
    sys.exit(1)

from src.domain.value_objects.audit_event import AuditEvent
from src.infrastructure.logging import get_logger, with_request_id
from src.infrastructure.logging.audit import log_audit_event
from src.infrastructure.monitoring.mcp_metrics import (
    record_mcp_request,
    set_registered_tools,
)
from src.infrastructure.monitoring.prometheus_metrics import get_metrics_registry

# Import MCP server
from src.presentation.mcp.server import mcp

# Configure logging
logger = get_logger(__name__)

# Create app first
app = FastAPI(
    title="AI Challenge MCP Server",
    description="HTTP wrapper for MCP protocol",
    version="1.0.0",
)

# Review routes initialization flag
_review_routes_initialized = False


class ToolCallRequest(BaseModel):
    """Request to call an MCP tool."""

    tool_name: str
    arguments: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    available_tools: int


def _get_tools_list() -> List[Dict[str, Any]]:
    """Get list of tools from mcp server directly.

    Returns:
        List of tool dictionaries with name, description, input_schema
    """
    tools = []
    try:
        # Access FastMCP's tool manager directly
        tool_manager = mcp._tool_manager
        logger.info(f"Tool manager has {len(tool_manager._tools)} tools")

        for tool_name, tool_info in tool_manager._tools.items():
            try:
                # Get description and input schema safely
                description = getattr(tool_info, "description", "") or ""

                # Get parameters (input schema) - FastMCP stores it in 'parameters'
                input_schema = {}
                if hasattr(tool_info, "parameters"):
                    params = tool_info.parameters
                    # Convert Pydantic model to dict if needed
                    if hasattr(params, "model_dump"):
                        input_schema = params.model_dump()
                    elif hasattr(params, "dict"):
                        input_schema = params.dict()
                    elif isinstance(params, dict):
                        input_schema = params
                    else:
                        # Try to serialize to JSON schema
                        if hasattr(params, "model_json_schema"):
                            input_schema = params.model_json_schema()
                        else:
                            input_schema = {}

                tools.append(
                    {
                        "name": tool_name,
                        "description": description,
                        "input_schema": input_schema,
                    }
                )
            except Exception as e:
                logger.warning(
                    f"Failed to serialize tool {tool_name}: {e}", exc_info=True
                )

        tools_count = len(tools)
        set_registered_tools(tools_count)
        logger.info(f"Returning {tools_count} tools")
    except Exception as e:
        logger.error(f"Failed to get tools list: {e}", exc_info=True)
    return tools


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        tools = _get_tools_list()

        # Add DB info for debugging
        try:
            from src.infrastructure.config.settings import get_settings

            settings = get_settings()
            logger.info(
                f"Health check: DB_NAME={settings.db_name}, MONGODB_URL={settings.mongodb_url}"
            )
        except Exception:
            pass

        return HealthResponse(status="healthy", available_tools=len(tools))
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(status="unhealthy", available_tools=0)


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    try:
        tools = _get_tools_list()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Tool discovery failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/call")
async def call_tool(tool_request: ToolCallRequest, http_request: Request):
    """Call an MCP tool."""
    tool_name = tool_request.tool_name
    start_time = perf_counter()
    status = "success"
    request_id = http_request.headers.get("X-Request-ID") or uuid4().hex
    actor = http_request.headers.get("X-Actor") or "mcp-http"
    client_ip = http_request.client.host if http_request.client else "unknown"

    with with_request_id(request_id):
        try:
            logger.info(
                f"Calling tool: {tool_name} with arguments: {str(tool_request.arguments)[:200]}"
            )
            result = await mcp._tool_manager.call_tool(tool_name, tool_request.arguments)
            logger.info(
                f"Tool call completed: {tool_name} (result type: {type(result).__name__})"
            )

            # Log result structure for debugging
            if isinstance(result, dict):
                logger.info(f"Result keys: {list(result.keys())}")
                if "digests" in result:
                    logger.info(f"Digests count: {len(result.get('digests', []))}")
                    if result.get("digests"):
                        for i, d in enumerate(result["digests"]):
                            logger.info(
                                f"Digest {i}: channel={d.get('channel')}, posts={d.get('post_count')}, summary_len={len(d.get('summary', ''))}"
                            )
                if "message" in result:
                    logger.info(f"Result message: {result['message'][:100]}")

            duration = perf_counter() - start_time
            record_mcp_request(tool_name, status, duration)
            log_audit_event(
                AuditEvent.create(
                    actor=actor,
                    action="mcp_tool_call",
                    resource=tool_name,
                    outcome="success",
                    metadata={
                        "duration_ms": round(duration * 1000, 2),
                        "client_ip": client_ip,
                        "arguments": list(tool_request.arguments.keys()),
                    },
                    trace_id=request_id,
                )
            )
            return {"result": result}
        except HTTPException as exc:
            status = "error" if exc.status_code >= 400 else "success"
            duration = perf_counter() - start_time
            record_mcp_request(tool_name, status, duration)
            log_audit_event(
                AuditEvent.create(
                    actor=actor,
                    action="mcp_tool_call",
                    resource=tool_name,
                    outcome="error" if exc.status_code >= 400 else "success",
                    metadata={
                        "status_code": exc.status_code,
                        "client_ip": client_ip,
                    },
                    trace_id=request_id,
                )
            )
            raise
        except Exception as e:
            status = "error"
            duration = perf_counter() - start_time
            record_mcp_request(tool_name, status, duration)
            logger.error(f"Tool call failed: {tool_name} - {str(e)}", exc_info=True)
            log_audit_event(
                AuditEvent.create(
                    actor=actor,
                    action="mcp_tool_call",
                    resource=tool_name,
                    outcome="error",
                    metadata={
                        "error": str(e)[:200],
                        "duration_ms": round(duration * 1000, 2),
                        "client_ip": client_ip,
                    },
                    trace_id=request_id,
                )
            )
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """Get server configuration for debugging."""
    try:
        from src.infrastructure.config.settings import get_settings

        settings = get_settings()

        # Also check actual DB connection
        try:
            from src.infrastructure.database.mongo import get_db

            db = await get_db()
            db_name = db.name
            posts_count = await db.posts.count_documents({})
            channels_count = await db.channels.count_documents({})
        except Exception as e:
            db_name = "error"
            posts_count = -1
            channels_count = -1
            logger.error(f"Failed to get DB info: {e}")

        return {
            "db_name": settings.db_name,
            "db_name_actual": db_name,
            "mongodb_url": settings.mongodb_url,
            "posts_in_db": posts_count,
            "channels_in_db": channels_count,
        }
    except Exception as e:
        logger.error(f"Config check failed: {e}", exc_info=True)
        return {"error": str(e)}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Challenge MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/config": "Server configuration",
            "/tools": "List available tools",
            "/call": "Call a tool (POST)",
            "/metrics": "Prometheus metrics",
            "/docs": "API documentation",
            "/api/v1/reviews": "Code review API",
        },
    }


# Review routes initialization function
async def _init_review_routes_async():
    """Initialize review routes with async dependencies."""
    logger.info("Starting review routes initialization...")
    try:
        from src.application.use_cases.enqueue_review_task_use_case import (
            EnqueueReviewTaskUseCase,
        )
        from src.application.use_cases.get_review_status_use_case import (
            GetReviewStatusUseCase,
        )
        from src.infrastructure.database.mongo import get_db
        from src.infrastructure.repositories.homework_review_repository import (
            HomeworkReviewRepository,
        )
        from src.infrastructure.repositories.long_tasks_repository import (
            LongTasksRepository,
        )
        from src.presentation.api.review_routes import create_review_router

        db = await get_db()
        tasks_repo = LongTasksRepository(db)
        review_repo = HomeworkReviewRepository(db)
        enqueue_use_case = EnqueueReviewTaskUseCase(tasks_repo)
        get_status_use_case = GetReviewStatusUseCase(tasks_repo, review_repo)

        from src.infrastructure.config.settings import get_settings

        settings = get_settings()
        review_router = create_review_router(
            enqueue_use_case, get_status_use_case, settings
        )
        app.include_router(review_router)
        logger.info("Review routes initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize review routes: {e}", exc_info=True)
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    try:
        from prometheus_client import (  # type: ignore
            CONTENT_TYPE_LATEST,
            generate_latest,
        )

        registry = get_metrics_registry()
        if registry is None:
            return Response(
                content="# Prometheus metrics not available\n", media_type="text/plain"
            )
        return Response(
            content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST
        )
    except ImportError:
        return Response(
            content="# Prometheus client not installed\n", media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}", exc_info=True)
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=500,
        )


def start_server(host: str = "0.0.0.0", port: int = 8004):
    """Start the HTTP server.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    # Allow port override from environment
    port = int(os.getenv("PORT", port))

    # Log configuration for debugging
    from src.infrastructure.config.settings import get_settings

    settings = get_settings()
    logger.info(f"Starting MCP HTTP server on {host}:{port}")
    logger.info(
        f"Server config: DB_NAME={settings.db_name}, MONGODB_URL={settings.mongodb_url}"
    )

    # Initialize review routes before starting server
    logger.info("Initializing review routes before server start...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_init_review_routes_async())
        loop.close()
        logger.info("Review routes initialized successfully before server start")
    except Exception as e:
        logger.warning(
            f"Failed to initialize review routes before server start: {e}",
            exc_info=True,
        )
        logger.warning("Review routes will be initialized on first request")

    run(
        app,
        host=host,
        port=port,
        log_level="info",
        timeout_keep_alive=300,  # Keep connections alive for long-running requests
        timeout_graceful_shutdown=60,
    )


if __name__ == "__main__":
    import os

    start_server()
