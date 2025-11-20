"""MCP presentation layer for tool discovery and execution."""

# Lazy imports to avoid MCP dependency when not needed.
try:
    from .client import MCPClient
    from .server import mcp
except ImportError:
    mcp = None
    MCPClient = None

__all__ = ["mcp", "MCPClient"]
