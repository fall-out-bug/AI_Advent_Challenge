# MCP Comprehensive Demo Guide

## Overview

The MCP Comprehensive Demo showcases all available tools in the AI Challenge MCP Server with full inputs and outputs documentation. This includes:

- Help and tool discovery
- Basic calculator operations
- Model discovery and availability checks
- Token analysis
- Code generation (simple and complex tasks)
- Code review, test generation, formatting, and complexity analysis
- Task formalization
- Tool chains demonstrating multi-step workflows

## Prerequisites

1. **Docker and Docker Compose**: Required for running local models
2. **MCP Server**: HTTP server running on port 8004
3. **Dependencies**: Python packages (asyncio, httpx, pytest)

## Starting the Demo Environment

### Option 1: Using Docker Compose (Recommended)

```bash
# Start MCP server with local models
docker-compose -f docker-compose.mcp-demo.yml up -d

# Wait for services to be healthy
docker-compose -f docker-compose.mcp-demo.yml ps

# Check logs if needed
docker-compose -f docker-compose.mcp-demo.yml logs -f mcp-server
```

### Option 2: Manual Start

```bash
# Start the HTTP server
python src/presentation/mcp/http_server.py
```

## Running the Demo

### Interactive Demo

Run the comprehensive interactive demo that shows all tools with inputs and outputs:

```bash
python scripts/mcp_comprehensive_demo.py
```

**What the demo shows:**
1. **Help and Discovery**: Lists all available tools with their descriptions and parameters
2. **Basic Tools**: Calculator, model discovery, token analysis
3. **Code Generation**: Simple and complex code generation tasks
4. **Code Analysis**: Review, testing, formatting, complexity analysis
5. **Tool Chains**: Multi-step workflows demonstrating tool orchestration

### Output Format

Each tool demonstration shows:
- **INPUT**: The tool name, arguments, and their values
- **OUTPUT**: The result, formatted and displayed clearly

Example output:
```
💻 Testing Code Generation
--------------------------------------------------------------------------------

INPUT:
  Tool: generate_code
  Arguments: description='create a simple function that adds two numbers', model='starcoder'

OUTPUT:
  Success: True
  Generated Code:
```python
def add(a, b):
    return a + b
```
  ✓ Code generation successful (34 characters)
```

## Running Tests

### Integration Tests

Run the comprehensive integration test suite:

```bash
# Run all tests
pytest tests/integration/test_mcp_comprehensive_demo.py -v

# Run specific test class
pytest tests/integration/test_mcp_comprehensive_demo.py::TestMCPTools -v

# Run specific test
pytest tests/integration/test_mcp_comprehensive_demo.py::TestMCPTools::test_generate_code_complex -v

# Run with detailed output
pytest tests/integration/test_mcp_comprehensive_demo.py -vv -s
```

### Test Coverage

The test suite includes:
- **TestMCPTools**: All 12 individual MCP tools with inputs/outputs
- **TestToolChains**: Multi-step workflows and tool chains
- **TestConversationContext**: Context-aware conversation simulation

## Available Tools

### 1. Calculator Tools
- `add(a, b)`: Add two numbers
- `multiply(a, b)`: Multiply two numbers

### 2. Model Discovery
- `list_models()`: List all available AI models
- `check_model(model_name)`: Check model availability

### 3. Token Analysis
- `count_tokens(text)`: Count tokens in text

### 4. Code Generation
- `generate_code(description, model)`: Generate Python code from description
- `generate_and_review(description, gen_model, review_model)`: Generate and review in one step

### 5. Code Analysis
- `review_code(code, model)`: Review code quality
- `analyze_complexity(code, detailed)`: Analyze code complexity

### 6. Test Generation
- `generate_tests(code, test_framework, coverage_target)`: Generate tests

### 7. Code Formatting
- `format_code(code, formatter, line_length)`: Format code

### 8. Task Formalization
- `formalize_task(informal_request, context)`: Convert informal request to structured plan

## Complex Code Generation Examples

### Example 1: Simple Calculator

**Input:**
```json
{
  "description": "create a simple calculator with add and multiply functions",
  "model": "starcoder"
}
```

**Expected Output:**
```python
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
```

### Example 2: REST API Class

**Input:**
```json
{
  "description": "Create a complete REST API class for user management with CRUD operations, validation, and error handling",
  "model": "starcoder"
}
```

**Expected Output:** Full REST API implementation with FastAPI, pydantic models, error handling, and validation.

## Tool Chains

### Chain 1: Generate → Review → Test

1. **Generate Code**: Create a calculator with add and multiply
2. **Review Code**: Analyze code quality and provide feedback
3. **Generate Tests**: Create pytest tests for the calculator

### Chain 2: Generate → Format → Analyze

1. **Generate Code**: Create a factorial function
2. **Format Code**: Apply Black formatter
3. **Analyze Complexity**: Calculate cyclomatic complexity

### Chain 3: Full Workflow

1. **Formalize Task**: Convert informal request to structured plan
2. **Generate Code**: Implement the plan
3. **Review Code**: Quality check
4. **Generate Tests**: Create comprehensive tests
5. **Analyze Complexity**: Evaluate maintainability

## Expected Input/Output Patterns

### Simple Tool (Calculator)

**Input:**
```json
{
  "tool_name": "add",
  "arguments": {"a": 10, "b": 25}
}
```

**Output:**
```json
{
  "result": 35.0
}
```

### Complex Tool (Code Generation)

**Input:**
```json
{
  "tool_name": "generate_code",
  "arguments": {
    "description": "create a function to calculate fibonacci sequence",
    "model": "starcoder"
  }
}
```

**Output:**
```json
{
  "result": {
    "success": true,
    "code": "def fibonacci(n): ...",
    "metadata": {
      "model": "starcoder",
      "tokens_used": 150,
      "generation_time": 2.5
    }
  }
}
```

## Troubleshooting

### Server Not Responding

```bash
# Check if server is running
curl http://localhost:8004/health

# Check logs
docker-compose -f docker-compose.mcp-demo.yml logs mcp-server

# Restart server
docker-compose -f docker-compose.mcp-demo.yml restart mcp-server
```

### Model Not Available

```bash
# Check model status
curl -X POST http://localhost:8004/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "check_model", "arguments": {"model_name": "starcoder"}}'

# List available models
curl http://localhost:8004/tools
```

### Test Failures

```bash
# Run with debug output
pytest tests/integration/test_mcp_comprehensive_demo.py -vv -s --tb=long

# Run single test
pytest tests/integration/test_mcp_comprehensive_demo.py::TestMCPTools::test_generate_code_simple -v
```

## API Reference

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "available_tools": 12
}
```

### GET /tools

List all available tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "add",
      "description": "Add two numbers",
      "input_schema": {
        "properties": {
          "a": {"type": "float", "description": "First number"},
          "b": {"type": "float", "description": "Second number"}
        },
        "required": ["a", "b"]
      }
    },
    ...
  ]
}
```

### POST /call

Call an MCP tool.

**Request:**
```json
{
  "tool_name": "generate_code",
  "arguments": {
    "description": "create a hello world function",
    "model": "starcoder"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "code": "def hello_world(): ..."
  }
}
```

## Next Steps

1. Explore individual tools by running the demo
2. Try creating custom tool chains
3. Experiment with complex code generation tasks
4. Review the test suite to understand expected behaviors
5. Check the MCP server source code for implementation details

## Additional Resources

- [MCP Server Source](src/presentation/mcp/server.py)
- [HTTP Server](src/presentation/mcp/http_server.py)
- [Integration Tests](tests/integration/test_mcp_comprehensive_demo.py)
- [Main README](README.md)

