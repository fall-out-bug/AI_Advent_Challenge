"""HTTP wrapper for MCP server using FastAPI."""
import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

# Add root to path for imports
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    from uvicorn import run
except ImportError:
    print("ERROR: fastapi and uvicorn required for HTTP mode")
    print("Install with: pip install fastapi uvicorn")
    sys.exit(1)

# Import MCP server
from src.presentation.mcp.server import mcp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Challenge MCP Server",
    description="HTTP wrapper for MCP protocol",
    version="1.0.0",
)


class ToolCallRequest(BaseModel):
    """Request to call an MCP tool."""
    tool_name: str
    arguments: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    available_tools: int


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Get available tools
        from src.presentation.mcp.client import MCPClient
        client = MCPClient()
        tools = await client.discover_tools()
        return HealthResponse(
            status="healthy",
            available_tools=len(tools)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            available_tools=0
        )


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    try:
        from src.presentation.mcp.client import MCPClient
        client = MCPClient()
        tools = await client.discover_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Tool discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/call")
async def call_tool(request: ToolCallRequest):
    """Call an MCP tool."""
    try:
        # Use the tool manager to call tools
        result = await mcp._tool_manager.call_tool(
            request.tool_name,
            request.arguments
        )
            
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool call failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Challenge MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/tools": "List available tools",
            "/call": "Call a tool (POST)",
            "/docs": "API documentation"
        }
    }


def start_server(host: str = "0.0.0.0", port: int = 8004):
    """Start the HTTP server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    logger.info(f"Starting MCP HTTP server on {host}:{port}")
    run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
