# Examples

This directory contains usage examples for the AI Challenge project.

## Available Examples

### Basic Usage

- `basic_usage.py` - Basic API and CLI operations
  - API health checks
  - CLI status and health
  - Metrics viewing
  - Configuration management

### Full Workflows

- `full_workflow.py` - Complete multi-step workflows
  - MCP tool discovery and execution
  - Mistral orchestration with conversation context
  - Multi-agent workflows

### MCP Examples

- `mcp/basic_discovery.py` - MCP tool discovery
  - Connect to MCP server
  - List available tools
  - Execute individual tools

## Usage

### Running Basic Examples

```bash
# Start API server (optional, for API examples)
python -m src.presentation.api

# Run basic examples
python examples/basic_usage.py
```

### Running Workflow Examples

```bash
# Ensure local_models docker-compose is running
cd local_models && docker-compose up -d

# Run full workflow examples
python examples/full_workflow.py
```

### Running MCP Examples

```bash
# Start MCP server (via Docker or local)
make mcp-server-start

# Run MCP discovery
python examples/mcp/basic_discovery.py
```

## Common Workflows

### Daily Operations

```bash
# Check system status
python -m src.presentation.cli.main_cli status

# Run health checks
python -m src.presentation.cli.main_cli health

# View metrics
python -m src.presentation.cli.main_cli metrics
```

### Development Workflow

```bash
# Run tests
make test

# Quality checks
./scripts/quality/run_all_checks.sh

# Format code
./scripts/quality/format_code.sh
```

## Additional Resources

- [Development Guide](../docs/DEVELOPMENT.md) - Complete setup and deployment guide
- [User Guide](../docs/USER_GUIDE.md) - User documentation
- [MCP Guide](../docs/MCP_GUIDE.md) - MCP integration guide
