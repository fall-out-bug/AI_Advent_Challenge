# Development & Deployment Guide

Complete guide for setting up, deploying, and operating the AI Challenge project.

## Overview

This guide covers local development setup, deployment options, operations, and troubleshooting for the AI Challenge project.

## Prerequisites

### Required Software

- **Python 3.10+** (for non-Docker deployment)
- **Poetry** (Python dependency management)
- **Docker & Docker Compose** (for containerized deployment)
- **Git** (version control)

### Optional Software

- VSCode or your preferred IDE
- Postman or curl (for API testing)

## Quick Start

### Clone and Install

```bash
git clone <repository-url>
cd AI_Challenge

# Install dependencies
poetry install

# Or with pip
pip install -r requirements.txt
```

### Set Environment Variables

```bash
# Copy example
cp api_key.txt.example api_key.txt

# Edit with your API key
nano api_key.txt
```

## Deployment Options

### Option 1: Docker Deployment (Recommended)

Docker provides isolation and consistent behavior across systems.

#### Start Services

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# Check status
docker ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# Test API
curl http://localhost:8000/docs
```

### Option 2: Non-Docker Deployment

For local development without Docker.

```bash
# Run API server
poetry run uvicorn src.presentation.api:app --reload

# Or with python module
poetry run python -m src.presentation.api
```

## Configuration

### Environment Variables

```bash
# Application settings
export STORAGE_PATH=./data
export MODEL_NAME=mistral
export MODEL_MAX_TOKENS=4096
export MODEL_TEMPERATURE=0.7
export PORT=8000
export LOG_LEVEL=INFO
```

### Configuration Files

- `config/models.yaml` - Model configurations
- `config/agents.yaml` - Agent configurations
- `api_key.txt` - API keys

Example model configuration:

```yaml
models:
  default: starcoder
  available:
    starcoder:
      max_input_tokens: 2048
      max_output_tokens: 1024
```

### Data Storage

Data is stored in the `data/` directory:
- `data/agents.json` - Agent task storage
- `data/experiments.json` - Experiment data

Ensure directory exists:

```bash
mkdir -p data
chmod 755 data
```

## Running the Application

### API Server

```bash
# Development mode (with auto-reload)
poetry run uvicorn src.presentation.api:app --reload

# Production mode
poetry run uvicorn src.presentation.api:app --host 0.0.0.0 --port 8000
```

### CLI Mode

```bash
# Code generation
poetry run python -m src.presentation.cli.main_cli generate "Create hello function"

# Code review
poetry run python -m src.presentation.cli.main_cli review code.py

# Status check
poetry run python -m src.presentation.cli.main_cli status
```

## Development Workflow

### Running Tests

```bash
# All tests
poetry run pytest src/tests

# Unit tests only
poetry run pytest src/tests/unit

# Integration tests
poetry run pytest src/tests/integration

# With coverage
poetry run pytest --cov=src src/tests
```

### Code Quality

```bash
# Run all checks
make test

# Format code
poetry run black src tests

# Lint
poetry run flake8 src tests

# Type check
poetry run mypy src
```

### Maintenance Tasks

```bash
# Cleanup old data
make maintenance-cleanup

# Create backup
make maintenance-backup

# Export data
make maintenance-export

# Validate system
make maintenance-validate
```

## Health Monitoring

### Health Checks

```bash
# Simple health check
curl http://localhost:8000/health

# Detailed readiness
curl http://localhost:8000/health/ready

# Model health
curl http://localhost:8000/health/models

# Storage health
curl http://localhost:8000/health/storage
```

### CLI Health

```bash
poetry run python -m src.presentation.cli.main_cli health
```

### Metrics Dashboard

Access the dashboard:
```
http://localhost:8000/dashboard/
```

## API Usage

### Code Generation

```bash
curl -X POST http://localhost:8000/api/agents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a hello world function",
    "agent_name": "test_agent"
  }'
```

### Code Review

```bash
curl -X POST http://localhost:8000/api/agents/review \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello(): pass",
    "agent_name": "test_agent"
  }'
```

### Metrics Export

```bash
# Export to JSON
poetry run python -m src.presentation.cli.main_cli metrics export json metrics.json

# Export to CSV
poetry run python -m src.presentation.cli.main_cli metrics export csv metrics.csv
```

## Troubleshooting

### Port Already in Use

**Solution 1 - Docker**:
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"
```

**Solution 2 - Non-Docker**:
```bash
export PORT=8001
poetry run uvicorn src.presentation.api:app --port 8001
```

### Import Errors

```bash
# Reinstall dependencies
poetry install

# Verify Python path
poetry run python -c "import src"

# Check for missing packages
poetry show
```

### Storage Permission Errors

```bash
# Fix permissions
chmod -R 755 data/

# Or recreate directory
rm -rf data/
mkdir data
chmod 755 data
```

### Docker Build Issues

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check Docker logs
docker-compose logs
```

### Health Check Failures

```bash
# Check API is running
curl http://localhost:8000/health

# View logs
docker-compose logs api

# Or for non-Docker, check terminal output
```

### Model Endpoint Issues

```bash
# Check model health
curl http://localhost:8000/health/models

# Check local models (if using)
curl http://localhost:8000/chat
curl http://localhost:8001/chat
curl http://localhost:8002/chat
```

### Performance Issues

**Check system resources**:
```bash
docker stats ai-challenge-api
poetry run python -m src.presentation.cli.main_cli metrics
```

## Operations

### Daily Maintenance

**Backup Data**:
```bash
make maintenance-backup
```

**Check Health**:
```bash
make maintenance-validate
```

### Weekly Maintenance

**Cleanup Old Data**:
```bash
# Preview what would be deleted
python -m scripts.maintenance.cleanup --days 30 --dry-run

# Actually clean up
python -m scripts.maintenance.cleanup --days 30
```

**Export Data**:
```bash
python -m scripts.maintenance.export_data --output exports/
```

### Monthly Maintenance

**Full Validation**:
```bash
./scripts/quality/run_all_checks.sh
```

**Update Dependencies**:
```bash
poetry show --outdated
poetry update
```

### Backup and Restore

**Create Backup**:
```bash
make maintenance-backup

# Or manually
python -m scripts.maintenance.backup
```

**Restore from Backup**:
```bash
python -m scripts.maintenance.backup --restore backups/backup_20240101.tar.gz
```

## Production Deployment

### Security Considerations

1. **API Keys**: Store in secure vault
2. **HTTPS**: Enable SSL/TLS
3. **Authentication**: Implement API auth
4. **Rate Limiting**: Prevent abuse
5. **CORS**: Configure appropriately

### Environment Configuration

```bash
# Development
export ENV=dev
export DEBUG=true

# Production
export ENV=prod
export DEBUG=false
export LOG_LEVEL=WARNING
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### Scaling

**Horizontal Scaling**:
```yaml
services:
  api:
    deploy:
      replicas: 3
```

**Load Balancing**: Use Traefik or Nginx.

## Performance Tuning

### Optimization Tips

1. **Async/Await**: Use throughout the application
2. **Connection Pooling**: Reuse database connections
3. **Caching**: Cache frequently accessed data
4. **Compression**: Enable gzip compression

### Resource Requirements

**Minimum**:
- CPU: 4+ cores
- RAM: 16GB+ (32GB for StarCoder)
- GPU: NVIDIA with 12GB+ VRAM (for StarCoder)
- Disk: 20GB+ (for models)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: poetry install
      - name: Run tests
        run: poetry run pytest src/tests/
      - name: Check coverage
        run: poetry run pytest --cov=src --cov-report=term
```

## FAQ

### General

**Q: What is the recommended hardware configuration?**

A: See [Resource Requirements](#resource-requirements).

**Q: How do I add a new model?**

A: Add configuration to `config/models.yaml`:

```yaml
models:
  my_model:
    base_url: http://localhost:8003
    max_tokens: 4096
    temperature: 0.7
```

### Configuration

**Q: How do I change the default model?**

A: Set environment variable:
```bash
export MODEL_NAME=mistral
```

### Troubleshooting

**Q: Why are health checks failing?**

A: Common causes:
1. API server not running
2. Storage not accessible
3. Model endpoints unreachable
4. Configuration errors

Run diagnosis:
```bash
python -m scripts.maintenance.validate
```

**Q: Why is the application slow?**

A: Check:
1. System resources (CPU, RAM, GPU)
2. Model response times
3. Network latency
4. Storage I/O

### Maintenance

**Q: How often should I backup data?**

A: Recommended schedule:
- Daily for production
- Weekly for development
- Before major changes

**Q: What should I do if the application crashes?**

A: Steps:
1. Check logs: `docker-compose logs api`
2. Validate configuration: `python -m scripts.maintenance.validate`
3. Check health: `curl http://localhost:8000/health`
4. Restart: `docker-compose restart api`
5. If persistent, restore from backup

## Additional Resources

- [API Documentation](http://localhost:8000/docs)
- [Architecture Guide](./ARCHITECTURE.md)
- [Testing Guide](./TESTING.md)
- [MCP Integration Guide](./MCP_GUIDE.md)

## Support

For issues and questions:
1. Check logs and health status
2. Run validation: `python -m scripts.maintenance.validate`
3. Review documentation in `docs/`
4. Check GitHub issues

