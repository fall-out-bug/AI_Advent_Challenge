# MCP API Reference

Complete API reference for all MCP tools exposed by the AI Challenge server.

## Table of Contents

- [Calculator Tools](#calculator-tools)
- [Model SDK Tools](#model-sdk-tools)
- [Agent Orchestration Tools](#agent-orchestration-tools)
- [Token Analysis Tools](#token-analysis-tools)
- [Response Schemas](#response-schemas)
- [Error Handling](#error-handling)

## Calculator Tools

### `add`

Add two numbers.

**Signature:**
```python
add(a: float, b: float) -> float
```

**Parameters:**
- `a` (float): First number
- `b` (float): Second number

**Returns:**
- `float`: Sum of a and b

**Example:**
```python
result = add(5.5, 3.2)  # Returns 8.7
```

### `multiply`

Multiply two numbers.

**Signature:**
```python
multiply(a: float, b: float) -> float
```

**Parameters:**
- `a` (float): First number
- `b` (float): Second number

**Returns:**
- `float`: Product of a and b

**Example:**
```python
result = multiply(4.0, 3.0)  # Returns 12.0
```

## Model SDK Tools

### `list_models`

List all available AI models.

**Signature:**
```python
async def list_models() -> ModelListResponse
```

**Returns:**
- `ModelListResponse`: Dictionary with `local_models` and `api_models` lists

**Example:**
```python
models = await list_models()
# Returns:
# {
#     "local_models": [
#         {"name": "mistral", "display_name": "Mistral-7B", ...},
#         {"name": "qwen", "display_name": "Qwen-4B", ...}
#     ],
#     "api_models": [
#         {"name": "perplexity", "provider": "Perplexity", ...}
#     ]
# }
```

### `check_model`

Check if a specific model is available.

**Signature:**
```python
async def check_model(model_name: str) -> ModelAvailabilityResponse
```

**Parameters:**
- `model_name` (str): Name of the model to check

**Returns:**
- `ModelAvailabilityResponse`: Dictionary with `available` boolean

**Example:**
```python
result = await check_model("mistral")
# Returns: {"available": True}
```

**Raises:**
- `MCPModelError`: If model check fails

## Agent Orchestration Tools

### `generate_code`

Generate Python code from description using AI agent.

**Signature:**
```python
async def generate_code(
    description: str,
    model: str = "mistral"
) -> CodeGenerationResponse
```

**Parameters:**
- `description` (str): Description of code to generate (required)
- `model` (str): Model to use (default: "mistral")

**Returns:**
- `CodeGenerationResponse`: Dictionary with generated code, tests, and metadata

**Example:**
```python
result = await generate_code(
    description="Create a function to calculate factorial",
    model="mistral"
)
# Returns:
# {
#     "success": True,
#     "code": "def factorial(n): ...",
#     "tests": "def test_factorial(): ...",
#     "metadata": {"complexity": "low", "lines_of_code": 10, ...}
# }
```

**Raises:**
- `MCPValidationError`: If description is empty or invalid
- `MCPAgentError`: If code generation fails

### `review_code`

Review Python code for quality and issues.

**Signature:**
```python
async def review_code(
    code: str,
    model: str = "mistral"
) -> CodeReviewResponse
```

**Parameters:**
- `code` (str): Python code to review (required)
- `model` (str): Model to use (default: "mistral")

**Returns:**
- `CodeReviewResponse`: Dictionary with review results and quality score

**Example:**
```python
result = await review_code(
    code='def hello(): print("world")',
    model="mistral"
)
# Returns:
# {
#     "success": True,
#     "quality_score": 8,
#     "issues": ["Missing type hints"],
#     "recommendations": ["Add return type annotation"],
#     "metadata": {"model_used": "mistral"}
# }
```

**Raises:**
- `MCPValidationError`: If code is empty or invalid
- `MCPAgentError`: If code review fails

### `generate_and_review`

Generate code and review it in a single workflow.

**Signature:**
```python
async def generate_and_review(
    description: str,
    gen_model: str = "mistral",
    review_model: str = "mistral"
) -> OrchestrationResponse
```

**Parameters:**
- `description` (str): Description of code to generate (required)
- `gen_model` (str): Model for generation (default: "mistral")
- `review_model` (str): Model for review (default: "mistral")

**Returns:**
- `OrchestrationResponse`: Dictionary with generation and review results

**Example:**
```python
result = await generate_and_review(
    description="Create a REST API endpoint",
    gen_model="mistral",
    review_model="mistral"
)
# Returns:
# {
#     "success": True,
#     "generation": {
#         "code": "@app.route('/api/data') ...",
#         "tests": "def test_endpoint(): ..."
#     },
#     "review": {
#         "score": 9,
#         "issues": [],
#         "recommendations": ["Add error handling"]
#     },
#     "workflow_time": 12.34
# }
```

**Raises:**
- `MCPValidationError`: If inputs are invalid
- `MCPOrchestrationError`: If workflow fails

## Token Analysis Tools

### `count_tokens`

Count tokens in text.

**Signature:**
```python
def count_tokens(text: str) -> TokenCountResponse
```

**Parameters:**
- `text` (str): Text to analyze

**Returns:**
- `TokenCountResponse`: Dictionary with token count

**Example:**
```python
result = count_tokens("Hello world, this is a test")
# Returns: {"count": 7}
```

## Response Schemas

All MCP tools return structured responses using Pydantic models:

### `MCPToolResponse` (Base)

Base response for all tools.

```python
{
    "success": bool,      # Whether the operation succeeded
    "error": str | None   # Error message if operation failed
}
```

### `CodeGenerationResponse`

```python
{
    "success": bool,
    "code": str,          # Generated code
    "tests": str,         # Generated tests
    "metadata": {
        "model_used": str,
        "complexity": str,
        "lines_of_code": int
    },
    "error": str | None
}
```

### `CodeReviewResponse`

```python
{
    "success": bool,
    "quality_score": int,       # Score 0-10
    "issues": list[str],        # Issues found
    "recommendations": list[str],  # Recommendations
    "review": str,              # Review text
    "metadata": {...},
    "error": str | None
}
```

### `OrchestrationResponse`

```python
{
    "success": bool,
    "generation": {
        "code": str,
        "tests": str
    },
    "review": {
        "score": int,
        "issues": list[str],
        "recommendations": list[str]
    },
    "workflow_time": float,     # Time in seconds
    "error": str | None
}
```

## Error Handling

All tools may raise domain-specific exceptions:

### Exception Types

- `MCPValidationError`: Invalid input
- `MCPModelError`: Model operation failed
- `MCPAgentError`: Agent operation failed
- `MCPOrchestrationError`: Workflow failed
- `MCPAdapterError`: Adapter operation failed
- `MCPBaseException`: Base exception for all MCP errors

### Exception Context

All exceptions include context information:

```python
try:
    result = await generate_code("")
except MCPValidationError as e:
    print(e.context["field"])  # "description"
```

## Usage Examples

### Complete Workflow Example

```python
from src.presentation.mcp.client import MCPClient

async def main():
    client = MCPClient()
    
    # 1. Check model availability
    model_status = await client.call_tool("check_model", {
        "model_name": "mistral"
    })
    
    # 2. Generate code
    code_result = await client.call_tool("generate_code", {
        "description": "Create a function to sort a list",
        "model": "mistral"
    })
    
    # 3. Review generated code
    review_result = await client.call_tool("review_code", {
        "code": code_result.get("code", ""),
        "model": "mistral"
    })
    
    # 4. Full workflow
    workflow_result = await client.call_tool("generate_and_review", {
        "description": "Create a REST API",
        "gen_model": "mistral",
        "review_model": "mistral"
    })
    
    print(f"Quality score: {workflow_result['review']['score']}/10")

asyncio.run(main())
```
