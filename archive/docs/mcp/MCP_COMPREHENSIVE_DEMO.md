# MCP Comprehensive Demo Guide

## Overview

This comprehensive demo tests all 12 MCP tools individually and in chains to verify the complete functionality of the MCP server running in Docker.

## Tools Tested (12 total)

### 1. Calculator Tools (2)
- `add(a, b)` - Basic addition
- `multiply(a, b)` - Basic multiplication

### 2. Utility Tools (3)
- `list_models()` - List available AI models
- `check_model(model_name)` - Check model availability
- `count_tokens(text)` - Count tokens in text

### 3. Code Generation & Review Tools (5)
- `generate_code(description, model)` - Generate Python code from description
- `review_code(code, model)` - Review code quality
- `generate_tests(code, test_framework, coverage_target)` - Generate unit tests
- `format_code(code, formatter, line_length)` - Format code with Black
- `analyze_complexity(code, detailed)` - Analyze code complexity metrics

### 4. Workflow Tools (2)
- `generate_and_review(description, gen_model, review_model)` - Combined generate + review
- `formalize_task(informal_request, context)` - Convert task to structured plan

## Running the Demo

### Prerequisites

1. Start the MCP server and required models:
   ```bash
   make mcp-server-start
   ```

2. Wait for all services to be healthy:
   ```bash
   docker ps
   # Check that mcp-server-day10 is "Up" and "healthy"
   ```

### Option 1: Interactive Demo Script

Run the comprehensive demo interactively:
```bash
make demo-mcp-comprehensive
```

This will:
- Test all 12 tools individually
- Demonstrate tool chains
- Show results with checkmarks for success
- Complete in ~5-10 minutes depending on model speed

### Option 2: Automated Test Suite

Run pytest integration tests:
```bash
make test-mcp-comprehensive
```

This will:
- Run all tool tests via pytest
- Test individual tools
- Test tool chains
- Test conversation context handling
- Show detailed test results

## Test Scenarios

### Individual Tool Tests

Each tool is tested with appropriate inputs:
- Calculator: math operations
- Model discovery: listing and checking models
- Token counting: text analysis
- Code generation: creating Python functions
- Code review: evaluating quality
- Test generation: creating unit tests
- Formatting: improving code style
- Complexity: analyzing metrics
- Task formalization: planning workflows

### Tool Chains

Three main chains are tested:

1. **Generate → Review → Test**
   - Generate code for a calculator
   - Review the generated code
   - Generate comprehensive tests

2. **Generate Compton Format → Analyze**
   - Generate code for a factorial function
   - Format the code with Black
   - Analyze complexity metrics

3. **Generate and Review Workflow**
   - Combined generate + review in one call

### Conversation Context

Tests verify that context is maintained across multiple messages:
- "build a calculator" → generates code
- "review it" → reviews the previously generated code
- "add tests for it" → generates tests for the code

## Expected Results

### Success Indicators

- ✅ All tools return valid responses
- ✅ Generated code is syntactically valid Python
- ✅ Code review provides meaningful feedback
- ✅ Generated tests include proper assertions
- ✅ Formatting improves code style
- ✅ Complexity metrics are reasonable (>0)
- ✅ Tool chains execute without errors
- ✅ Conversation context is preserved

### Response Times

- Calculator tools: <1 second
- Model discovery: <1 second
- Token counting: <1 second
- Code generation: 10-30 seconds
- Code review: 10-30 seconds
- Test generation: 15-40 seconds
- Code formatting: <1 second
- Complexity analysis: <1 second
- Task formalization: 10-30 seconds

## Troubleshooting

### MCP Server Not Running

If you see connection errors:
```bash
# Check server status
docker ps | grep mcp-server

# Start the server
make mcp-server-start

# Check logs
docker logs mcp-server-day10
```

### Models Not Responding

If code generation fails:
```bash
# Check model containers
docker ps | grep -E "mistral|starcoder"

# Check model logs
docker logs mistral-chat
docker logs starcoder-chat

# Restart models
docker-compose -f docker-compose.mcp-demo.yml restart mistral-chat starcoder-chat
```

### Slow Responses

If tests are timing out:
- Large models take time to load initially
- First request per model may be slower (cold start)
- Increase timeout in test files if needed (currently 300 seconds)

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: MCP Comprehensive Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: make mcp-server-start
      - name: Wait for services
        run: sleep 60
      - name: Run tests
        run: make test-mcp-comprehensive
      - name: Stop services
        run: make mcp-server-stop
```

## Files

- **Test Suite**: `tests/integration/test_mcp_comprehensive_demo.py`
- **Demo Script**: `scripts/mcp_comprehensive_demo.py`
- **Make Targets**: `Makefile`
- **Documentation**: This file

## Next Steps

After running the comprehensive demo, you can:

1. Use individual tools via the HTTP API:
   ```bash
   curl -X POST http://localhost:8004/call \
     -H "Content-Type: application/json" \
     -d '{"tool_name": "generate_code", "arguments": {"description": "create a hello world function"}}'
   ```

2. Use the streaming chat with tool chains:
   ```bash
   make mcp-chat-docker
   ```

3. Build custom workflows combining multiple tools

## Success Criteria

All tools should:
- ✅ Execute successfully via HTTP
- ✅ Return valid response structures
- ✅ Handle errors gracefully
- ✅ Support conversation context
- ✅ Work in tool chains
- ✅ Complete within timeout limits

Monitoring and logging are available via Docker logs for debugging and performance analysis.
