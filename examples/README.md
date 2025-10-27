# Examples

This directory contains usage examples for the AI Challenge project.

## Available Examples

### CLI Examples

- `cli_basic.py` - Basic CLI operations
  - Status checks
  - Health checks
  - Metrics viewing
  - Configuration management

### API Examples

- `api_basic.py` - Basic API operations
  - Health checks
  - Readiness checks
  - Metrics retrieval
  - Dashboard access

## Usage

### Running CLI Examples

```bash
# Basic CLI example
python examples/cli_basic.py

# Or run CLI directly
python -m src.presentation.cli.main_cli status
python -m src.presentation.cli.main_cli health
python -m src.presentation.cli.main_cli metrics
```

### Running API Examples

```bash
# Start API server first
python -m src.presentation.api

# Then run examples
python examples/api_basic.py
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

### Maintenance Tasks

```bash
# Create backup
make maintenance-backup

# Clean up old data
python -m scripts.maintenance.cleanup --days 30 --dry-run

# Export data
python -m scripts.maintenance.export_data

# Validate system
python -m scripts.maintenance.validate
```

### Development Workflow

```bash
# Run quality checks
./scripts/quality/run_all_checks.sh

# Format code
./scripts/quality/format_code.sh

# Check coverage
python -m scripts.quality.check_coverage
```

## More Examples

See documentation for more detailed examples:
- [Operations Guide](../docs/OPERATIONS.md)
- [Local Deployment Guide](../docs/LOCAL_DEPLOYMENT.md)

