# Local Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the AI Challenge project locally, with options for both Docker and non-Docker setups.

## Prerequisites

### Required Software

- **Python 3.10+** (for non-Docker deployment)
- **Poetry** (Python dependency management)
- **Docker & Docker Compose** (for containerized deployment)
- **Git** (version control)

### Optional Software

- **VSCode** or your preferred IDE
- **Postman** or **curl** (for API testing)

## Setup Options

### Option 1: Docker Deployment (Recommended)

Docker deployment provides an isolated environment and consistent behavior across different systems.

#### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd AI_Challenge
```

#### Step 2: Build Docker Image

```bash
docker-compose build
```

#### Step 3: Start Services

```bash
docker-compose up -d
```

#### Step 4: Verify Deployment

```bash
# Check if container is running
docker ps

# Check health
curl http://localhost:8000/health/

# View logs
docker-compose logs -f
```

#### Step 5: Stop Services

```bash
docker-compose down
```

### Option 2: Non-Docker Deployment

For local development without Docker.

#### Step 1: Install Dependencies

```bash
poetry install
```

#### Step 2: Set Environment Variables

```bash
export STORAGE_PATH=./data
export MODEL_NAME=gpt-4
export MODEL_MAX_TOKENS=4096
export MODEL_TEMPERATURE=0.7
```

Or create a `.env` file:

```env
STORAGE_PATH=./data
MODEL_NAME=gpt-4
MODEL_MAX_TOKENS=4096
MODEL_TEMPERATURE=0.7
```

#### Step 3: Run Application

```bash
# Start API server
poetry run python -m src.presentation.api

# Or use uvicorn directly
poetry run uvicorn src.presentation.api:app --reload
```

#### Step 4: Verify Deployment

```bash
# Check health
curl http://localhost:8000/health/

# View API docs
open http://localhost:8000/docs
```

## Configuration

### Application Settings

Configure the application via environment variables or `config/` files:

**Environment Variables**:
- `STORAGE_PATH` - Path to data storage (default: `./data`)
- `MODEL_NAME` - Default model name (default: `gpt-4`)
- `MODEL_MAX_TOKENS` - Max tokens per request (default: `4096`)
- `MODEL_TEMPERATURE` - Model temperature (default: `0.7`)

**Configuration Files**:
- `config/models.yaml` - Model configurations
- `config/agents.yaml` - Agent configurations

### Data Storage

Data is stored in the `data/` directory:
- `data/agents.json` - Agent task storage
- `data/experiments.json` - Experiment data

Ensure the storage directory exists:

```bash
mkdir -p data
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

### Code Quality Checks

```bash
# Run all checks
./scripts/quality/run_all_checks.sh

# Quick check (no tests)
./scripts/quality/quick_check.sh

# Format code
./scripts/quality/format_code.sh

# Check coverage
poetry run python -m scripts.quality.check_coverage
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

## API Usage

### Health Checks

```bash
# Simple health check
curl http://localhost:8000/health/

# Detailed readiness
curl http://localhost:8000/health/ready

# Model health
curl http://localhost:8000/health/models

# Storage health
curl http://localhost:8000/health/storage
```

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

### Dashboard

Visit the metrics dashboard:
```
http://localhost:8000/dashboard/
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

**Docker**:
```bash
# Use different port
docker-compose up -p 8001:8000
```

**Non-Docker**:
```bash
# Set port via environment
export PORT=8001
poetry run uvicorn src.presentation.api:app --port 8001
```

### Docker Build Issues

If Docker build fails:

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Import Errors

If you encounter import errors:

```bash
# Reinstall dependencies
poetry install

# Verify Python path
poetry run python -c "import src"
```

### Storage Permission Errors

If storage is not writable:

```bash
# Fix permissions
chmod -R 755 data/
```

### Health Check Failures

If health checks fail:

```bash
# Check API is running
curl http://localhost:8000/health/

# View logs
docker-compose logs api

# Or for non-Docker
# Check terminal output
```

## Performance Tuning

### For Local Development

**Docker**:
- Adjust CPU/memory limits in `docker-compose.yml`
- Reduce health check frequency if needed

**Non-Docker**:
- Use `--reload` flag for development
- Set `PYTHONOPTIMIZE=1` for production

### Resource Limits

Configure in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## Monitoring

### Metrics Dashboard

Access the metrics dashboard:
```
http://localhost:8000/dashboard/
```

### Logs

**Docker**:
```bash
docker-compose logs -f api
```

**Non-Docker**:
Check terminal output or log files

### Health Monitoring

Monitor health via CLI:
```bash
python -m src.presentation.cli.main_cli health
```

## Next Steps

1. Explore the API documentation at `/docs`
2. Try the example workflows
3. Customize model configurations
4. Set up your own agents

## Additional Resources

- [API Documentation](http://localhost:8000/docs)
- [Maintenance Guide](../README.md#maintenance)
- [Configuration Reference](./CONFIGURATION.md)


