# Day 12 - Testing and Launch Guide

**Date**: Phase 8 Implementation  
**Status**: ✅ Ready for Testing  
**Approach**: Comprehensive testing and deployment guide

## Overview

This guide covers testing and launching Day 12 project, including all components: post fetcher worker, PDF digest generation, and Prometheus monitoring.

## Prerequisites

### Required Software

- Python 3.10+
- Docker Engine 20.10+ and Docker Compose 2.0+
- MongoDB 6.0+ (or use Docker Compose service)
- Poetry (for Python dependency management)

### Required Environment Variables

Create `.env` file in project root:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_STRING=your_session_string

# HuggingFace Token
HF_TOKEN=your_hf_token_here

# MongoDB Configuration
MONGODB_URL=mongodb://mongodb:27017
DB_NAME=butler

# LLM Configuration
LLM_URL=http://mistral-chat:8000

# Post Fetcher Worker Configuration
POST_FETCH_INTERVAL_HOURS=1
POST_TTL_DAYS=7

# Logging
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
poetry install

# Or with pip
pip install -r requirements.txt  # If requirements.txt exists
```

### 2. Run Tests

```bash
# Run all tests
python scripts/day12_run.py test --type all

# Run specific test types
python scripts/day12_run.py test --type unit
python scripts/day12_run.py test --type integration
python scripts/day12_run.py test --type metrics

# Or use pytest directly
pytest tests/workers/test_post_fetcher_worker.py -v
pytest src/tests/presentation/mcp/test_pdf_digest_tools.py -v
pytest tests/integration/test_pdf_digest_flow.py -v
pytest src/tests/infrastructure/monitoring/test_prometheus_metrics.py -v
```

### 3. Start Services

```bash
# Start all services
python scripts/day12_run.py start

# Or manually
docker-compose -f docker-compose.day12.yml up -d
```

### 4. Check Service Health

```bash
# Check service status
python scripts/day12_run.py check

# Or manually
docker-compose -f docker-compose.day12.yml ps
```

### 5. View Metrics

```bash
# View Prometheus metrics
python scripts/day12_run.py metrics

# Or directly
curl http://localhost:8004/metrics
```

## Testing Strategy

### Unit Tests

**Location**: `tests/workers/`, `src/tests/presentation/mcp/`

**Coverage**:
- Post Fetcher Worker: Channel processing, error handling, schedule logic
- PDF Digest Tools: All 5 MCP tools (get_posts_from_db, summarize_posts, format_digest_markdown, combine_markdown_sections, convert_markdown_to_pdf)
- Prometheus Metrics: Metrics collection and export

**Run**:
```bash
pytest tests/workers/test_post_fetcher_worker.py -v
pytest src/tests/presentation/mcp/test_pdf_digest_tools.py -v
pytest src/tests/infrastructure/monitoring/test_prometheus_metrics.py -v
```

### Integration Tests

**Location**: `tests/integration/test_pdf_digest_flow.py`

**Coverage**:
- Full PDF digest flow from post collection to PDF generation
- MongoDB integration
- Error handling and edge cases

**Run**:
```bash
pytest tests/integration/test_pdf_digest_flow.py -v
```

**Requirements**:
- MongoDB running (use `mongodb://localhost:27017`)
- Test database: `butler_test`

### End-to-End Tests

**Location**: `tests/e2e/`

**Coverage**:
- Complete bot workflow
- User interaction flows
- PDF generation and delivery

**Run**:
```bash
pytest tests/e2e/ -v
```

## Service Testing

### Post Fetcher Worker

**Manual Test**:
```bash
# Check logs
python scripts/day12_run.py logs post-fetcher-worker

# Or directly
docker-compose -f docker-compose.day12.yml logs -f post-fetcher-worker
```

**Verify**:
- Worker starts successfully
- Processes channels hourly
- Saves posts to MongoDB
- Logs statistics

### MCP Server

**Manual Test**:
```bash
# Check health
curl http://localhost:8004/health

# View metrics
curl http://localhost:8004/metrics

# List tools
curl http://localhost:8004/tools
```

**Verify**:
- Health endpoint returns 200
- Metrics endpoint returns Prometheus format
- All PDF tools are available

### Telegram Bot

**Manual Test**:
1. Start bot via Docker Compose
2. Send `/menu` command to bot
3. Click "Digest" button
4. Verify PDF is generated and sent

**Verify**:
- Bot responds to commands
- PDF digest generation works
- PDF file is sent correctly

## Metrics Testing

### Prometheus Metrics

**Available Metrics**:

1. **Post Fetcher Worker**:
   - `post_fetcher_posts_saved_total`
   - `post_fetcher_channels_processed_total`
   - `post_fetcher_errors_total`
   - `post_fetcher_duration_seconds`
   - `post_fetcher_worker_running`
   - `post_fetcher_last_run_timestamp_seconds`

2. **PDF Generation**:
   - `pdf_generation_duration_seconds`
   - `pdf_generation_errors_total`
   - `pdf_file_size_bytes`
   - `pdf_pages_total`

3. **Bot Digest Handler**:
   - `bot_digest_requests_total`
   - `bot_digest_cache_hits_total`
   - `bot_digest_errors_total`

**Test Metrics Collection**:
```bash
# View metrics
python scripts/day12_run.py metrics

# Test specific metric
curl http://localhost:8004/metrics | grep post_fetcher
curl http://localhost:8004/metrics | grep pdf_generation
curl http://localhost:8004/metrics | grep bot_digest
```

## Troubleshooting

### Tests Fail

**Issue**: Tests fail with import errors

**Solution**:
```bash
# Install dependencies
poetry install

# Or
pip install prometheus-client pytest pytest-asyncio
```

**Issue**: MongoDB connection errors in integration tests

**Solution**:
```bash
# Start MongoDB
docker-compose -f docker-compose.day12.yml up -d mongodb

# Or use local MongoDB
export MONGODB_URL=mongodb://localhost:27017
export DB_NAME=butler_test
```

### Services Won't Start

**Issue**: Docker Compose fails

**Solution**:
```bash
# Check Docker is running
docker ps

# Check Docker Compose version
docker-compose --version

# Rebuild images
docker-compose -f docker-compose.day12.yml build --no-cache
```

**Issue**: Service health checks fail

**Solution**:
```bash
# Check service logs
python scripts/day12_run.py logs <service-name>

# Check environment variables
docker-compose -f docker-compose.day12.yml config
```

### Metrics Not Available

**Issue**: Metrics endpoint returns 404

**Solution**:
```bash
# Check prometheus-client is installed
pip list | grep prometheus-client

# Check MCP server logs
python scripts/day12_run.py logs mcp-server

# Verify metrics module imports
python -c "from src.infrastructure.monitoring.prometheus_metrics import get_metrics_registry; print(get_metrics_registry())"
```

## Deployment Checklist

Before deploying to production:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All services start successfully
- [ ] Health checks pass
- [ ] Metrics endpoint accessible
- [ ] MongoDB indexes created
- [ ] Environment variables configured
- [ ] Docker images built
- [ ] Resource limits appropriate
- [ ] Logging configured

## Performance Testing

### Load Testing

**Post Fetcher Worker**:
```bash
# Test with many channels
# Create test channels in MongoDB
# Monitor processing time via metrics
```

**PDF Generation**:
```bash
# Generate multiple PDFs
# Monitor duration and error rates
# Check memory usage
```

### Monitoring

**View Metrics**:
```bash
# Real-time metrics
watch -n 5 'curl -s http://localhost:8004/metrics | grep -E "(post_fetcher|pdf_generation|bot_digest)"'
```

**View Logs**:
```bash
# All services
python scripts/day12_run.py logs

# Specific service
python scripts/day12_run.py logs post-fetcher-worker
```

## Continuous Integration

### CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Day 12 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: poetry install
      - name: Run unit tests
        run: pytest tests/workers/test_post_fetcher_worker.py -v
      - name: Run integration tests
        run: pytest tests/integration/test_pdf_digest_flow.py -v
      - name: Run metrics tests
        run: pytest src/tests/infrastructure/monitoring/test_prometheus_metrics.py -v
```

## Support

For issues:
1. Check logs: `python scripts/day12_run.py logs`
2. Check metrics: `python scripts/day12_run.py metrics`
3. Check service status: `python scripts/day12_run.py check`
4. Review documentation: `docs/day12/DEPLOYMENT.md`

## Next Steps

After successful testing:
1. Deploy to staging environment
2. Configure Prometheus scraping
3. Set up alerting (AlertManager)
4. Create Grafana dashboards
5. Monitor production metrics

