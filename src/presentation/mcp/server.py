"""FastMCP server exposing AI Challenge capabilities."""

import os
from pathlib import Path
from typing import Any, Dict

from mcp.server import fastmcp

FastMCP = fastmcp.FastMCP

# Create FastMCP server
mcp = FastMCP(
    "AI Challenge MCP Server",
    instructions="Expose SDK and agent capabilities via MCP protocol",
)


# Register tools AFTER mcp is created to avoid circular imports
# Import modules so their @mcp.tool decorators execute and register tools
def _register_all_tools() -> None:
    """Register all tool modules by importing them."""

    from src.infrastructure.logging import get_logger
    from src.infrastructure.monitoring.mcp_metrics import set_registered_tools

    include_deprecated = os.getenv(
        "MCP_INCLUDE_DEPRECATED_TOOLS", "0"
    ).lower() not in {"", "0", "false", "no"}

    tool_modules = [
        ("nlp_tools", "src.presentation.mcp.tools.nlp_tools", "supported", ""),
        (
            "digest_tools",
            "src.presentation.mcp.tools.digest_tools",
            "supported",
            "",
        ),
        (
            "channels",
            "src.presentation.mcp.tools.channels",
            "supported",
            "Channel bulk management migrates to CLI backoffice in Stage 02_02.",
        ),
        (
            "pdf_digest_tools",
            "src.presentation.mcp.tools.pdf_digest_tools",
            "deprecated",
            "CLI `digest:export` replaces this tool during Stage 02_02.",
        ),
        (
            "homework_review_tool",
            "src.presentation.mcp.tools.homework_review_tool",
            "deprecated",
            "Modular reviewer replacement ships after EP01 refactor.",
        ),
    ]

    logger = get_logger(__name__)

    for name, module_path, status, note in tool_modules:
        if status == "deprecated" and not include_deprecated:
            logger.info(
                "Skipping deprecated MCP tool %s (enable MCP_INCLUDE_DEPRECATED_TOOLS "
                "to register).",
                name,
            )
            continue

        try:
            __import__(module_path)
            if status == "deprecated":
                logger.warning("Registered deprecated MCP tool %s: %s", name, note)
            else:
                logger.info("Registered tools from %s", name)
            if note and status != "deprecated":
                logger.debug(note)
        except Exception as exc:
            logger.error(
                "Failed to import %s from %s: %s", name, module_path, exc, exc_info=True
            )

    try:
        tools_registered = len(mcp._tool_manager._tools)
    except AttributeError:
        tools_registered = 0
    set_registered_tools(tools_registered)

# Register tools immediately when module loads
_register_all_tools()

from src.presentation.mcp.prompts.code_review import code_review_prompt
from src.presentation.mcp.prompts.test_generation import test_generation_prompt

# Import MCP resources and prompts
from src.presentation.mcp.resources.prompts import (
    get_architect_prompt,
    get_coding_standards,
    get_python_developer_prompt,
    get_technical_writer_prompt,
)
from src.presentation.mcp.resources.templates import (
    get_class_template,
    get_project_structure_template,
    get_pytest_template,
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


# Task Formalization Tool
@mcp.tool()
async def formalize_task(informal_request: str, context: str = "") -> Dict[str, Any]:
    """Convert informal request into a structured development plan.

    Args:
        informal_request: Natural language description of the task
        context: Additional context or constraints

    Returns:
        Structured plan with requirements and steps
    """
    adapter = get_adapter()
    return await adapter.formalize_task(informal_request, context)


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
async def generate_code(description: str, model: str = "starcoder") -> Dict[str, Any]:
    """Generate Python code from description using AI agent.

    Args:
        description: Description of code to generate
        model: Model to use (default: starcoder - specialized for code generation)

    Returns:
        Dictionary with generated code and metadata
    """
    adapter = get_adapter()
    return await adapter.generate_code_via_agent(description, model)


@mcp.tool()
async def review_code(code: str, model: str = "starcoder") -> Dict[str, Any]:
    """Review Python code for quality and issues.

    Args:
        code: Python code to review
        model: Model to use (default: starcoder)

    Returns:
        Dictionary with review results and quality score
    """
    adapter = get_adapter()
    return await adapter.review_code_via_agent(code, model)


@mcp.tool()
async def generate_and_review(
    description: str,
    gen_model: str = "starcoder",
    review_model: str = "starcoder",
) -> Dict[str, Any]:
    """Generate code and review it in single workflow.

    Args:
        description: Description of code to generate
        gen_model: Model for generation (default: starcoder)
        review_model: Model for review (default: starcoder)

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


# Test Generation Tool
@mcp.tool()
async def generate_tests(
    code: str, test_framework: str = "pytest", coverage_target: int = 80
) -> Dict[str, Any]:
    """Generate comprehensive tests for provided code.

    Args:
        code: Source code to generate tests for
        test_framework: Testing framework (pytest, unittest, etc.)
        coverage_target: Target coverage percentage

    Returns:
        Dictionary with test code, test count, and coverage estimate
    """
    adapter = get_adapter()
    return await adapter.generate_tests(code, test_framework, coverage_target)


# Code Formatting Tool
@mcp.tool()
def format_code(
    code: str, formatter: str = "black", line_length: int = 100
) -> Dict[str, Any]:
    """Format code according to style guidelines.

    Args:
        code: Code to format
        formatter: Formatter to use (black, autopep8, etc.)
        line_length: Maximum line length

    Returns:
        Dictionary with formatted code and changes made
    """
    adapter = get_adapter()
    return adapter.format_code(code, formatter, line_length)


# Complexity Analysis Tool
@mcp.tool()
def analyze_complexity(code: str, detailed: bool = True) -> Dict[str, Any]:
    """Analyze code complexity metrics.

    Args:
        code: Code to analyze
        detailed: Include detailed analysis

    Returns:
        Dictionary with complexity metrics and recommendations
    """
    adapter = get_adapter()
    return adapter.analyze_complexity(code, detailed)


# MCP Resources
@mcp.resource("prompts://python-developer")
def python_developer_resource() -> str:
    """Python developer system prompt."""
    return get_python_developer_prompt()


@mcp.resource("prompts://architect")
def architect_resource() -> str:
    """Software architect system prompt."""
    return get_architect_prompt()


@mcp.resource("prompts://technical-writer")
def technical_writer_resource() -> str:
    """Technical writer system prompt."""
    return get_technical_writer_prompt()


@mcp.resource("config://coding-standards")
def coding_standards_resource() -> str:
    """Coding standards configuration."""
    return get_coding_standards()


@mcp.resource("templates://project-structure")
def project_structure_resource() -> str:
    """Standard project structure template."""
    return get_project_structure_template()


@mcp.resource("templates://pytest")
def pytest_template_resource() -> str:
    """Pytest test template."""
    return get_pytest_template()


@mcp.resource("templates://python-class")
def class_template_resource() -> str:
    """Python class template."""
    return get_class_template()


# MCP Dynamic Prompts
@mcp.prompt("code-review")
def code_review_prompt_resource(
    code: str, language: str = "python", style: str = "pep8"
) -> str:
    """Generate code review prompt dynamically.

    Args:
        code: Code to review
        language: Programming language
        style: Style guide
    """
    return code_review_prompt(code, language, style)


@mcp.prompt("test-generation")
def test_generation_prompt_resource(code: str, framework: str = "pytest") -> str:
    """Generate test generation prompt dynamically.

    Args:
        code: Code to generate tests for
        framework: Testing framework
    """
    return test_generation_prompt(code, framework)


if __name__ == "__main__":
    # Run MCP server via stdio
    mcp.run()
