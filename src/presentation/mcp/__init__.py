"""MCP presentation layer for tool discovery and execution."""
from .server import mcp
from .client import MCPClient

__all__ = ["mcp", "MCPClient"]

