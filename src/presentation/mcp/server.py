"""FastMCP server exposing AI Challenge capabilities."""
import sys
from pathlib import Path
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP

# Add root to path for imports when running as script
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))

# Create FastMCP server
mcp = FastMCP(
    "AI Challenge MCP Server",
    instructions="Expose SDK and agent capabilities via MCP protocol",
)

# Import adapters lazily to avoid circular imports
_adapters_module = None

def _get_adapters_module():
    """Lazy import of adapters module."""
    import importlib.util
    global _adapters_module
    if _adapters_module is None:
        # Import the actual adapters.py file (not the package __init__)
        adapters_path = Path(__file__).parent / "adapters.py"
        spec = importlib.util.spec_from_file_location("mcp_adapters", adapters_path)
        _adapters_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_adapters_module)
    return _adapters_module

# Initialize adapter (will be singleton)
_adapter = None


def get_adapter():
    """Get or create adapter instance.

    Returns:
        MCP application adapter
    """
    global _adapter
    if _adapter is None:
        adapters = _get_adapters_module()
        _adapter = adapters.MCPApplicationAdapter()
    return _adapter


# Calculator Tools (Demo)
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b
    """
    return a * b


# Model SDK Tools
@mcp.tool()
async def list_models() -> Dict[str, list]:
    """List all available AI models.

    Returns:
        Dictionary containing local and external model lists
    """
    adapter = get_adapter()
    return await adapter.list_available_models()


@mcp.tool()
async def check_model(model_name: str) -> Dict[str, bool]:
    """Check if a specific model is available.

    Args:
        model_name: Name of the model to check

    Returns:
        Dictionary with availability status
    """
    adapter = get_adapter()
    return await adapter.check_model_availability(model_name)


# Agent Orchestration Tools
@mcp.tool()
async def generate_code(description: str, model: str = "mistral") -> Dict[str, Any]:
    """Generate Python code from description using AI agent.

    Args:
        description: Description of code to generate
        model: Model to use (default: mistral)

    Returns:
        Dictionary with generated code and metadata
    """
    adapter = get_adapter()
    return await adapter.generate_code_via_agent(description, model)


@mcp.tool()
async def review_code(code: str, model: str = "mistral") -> Dict[str, Any]:
    """Review Python code for quality and issues.

    Args:
        code: Python code to review
        model: Model to use (default: mistral)

    Returns:
        Dictionary with review results and quality score
    """
    adapter = get_adapter()
    return await adapter.review_code_via_agent(code, model)


@mcp.tool()
async def generate_and_review(
    description: str,
    gen_model: str = "mistral",
    review_model: str = "mistral",
) -> Dict[str, Any]:
    """Generate code and review it in single workflow.

    Args:
        description: Description of code to generate
        gen_model: Model for generation (default: mistral)
        review_model: Model for review (default: mistral)

    Returns:
        Dictionary with generation and review results
    """
    adapter = get_adapter()
    return await adapter.orchestrate_generation_and_review(
        description, gen_model, review_model
    )


# Token Analysis Tool
@mcp.tool()
def count_tokens(text: str) -> Dict[str, int]:
    """Count tokens in text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with token count
    """
    adapter = get_adapter()
    return adapter.count_text_tokens(text)


if __name__ == "__main__":
    # Run MCP server via stdio
    mcp.run()

