"""MCP presentation layer for tool discovery and execution."""
# Lazy imports to avoid MCP dependency when not needed.
try:
    from .server import mcp
    from .client import MCPClient
except ImportError:
    mcp = None
    MCPClient = None

__all__ = ["mcp", "MCPClient"]

