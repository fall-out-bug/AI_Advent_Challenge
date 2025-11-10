"""Simple healthcheck script for MCP server."""

import sys
from pathlib import Path

# Add root to path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))

try:
    # Just verify imports work - actual discovery requires external MCP client
    import src.presentation.mcp.server as mcp_module
    print("MCP server module loaded successfully")
    sys.exit(0)
except Exception as e:
    print(f"Healthcheck failed: {e}")
    sys.exit(1)
