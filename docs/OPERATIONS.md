# Operations Guide

## Overview

This guide covers common operations, troubleshooting, and maintenance procedures for the AI Challenge project.

## Table of Contents

- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)
- [Maintenance Procedures](#maintenance-procedures)
- [FAQ](#faq)

## Common Operations

### Starting the Application

**With Docker**:
```bash
# Start all services
docker-compose up -d

# Check status
docker ps

# View logs
docker-compose logs -f api
```

**Without Docker**:
```bash
# Start API server
poetry run python -m src.presentation.api

# Or with reload for development
poetry run uvicorn src.presentation.api:app --reload
```

### Health Checks

**API Health Check**:
```bash
# Simple check
curl http://localhost:8000/health/

# Detailed readiness
curl http://localhost:8000/health/ready

# Model health
curl http://localhost:8000/health/models

# Storage health
curl http://localhost:8000/health/storage
```

**CLI Health Check**:
```bash
python -m src.presentation.cli.main_cli health
```

### Viewing Metrics

**API Dashboard**:
```
http://localhost:8000/dashboard/
```

**CLI Status**:
```bash
python -m src.presentation.cli.main_cli status
```

**Export Metrics**:
```bash
# Export to JSON
python -m src.presentation.cli.main_cli metrics export json metrics.json

# Export to CSV
python -m src.presentation.cli.main_cli metrics export csv metrics.csv
```

### Configuration Management

**View Configuration**:
```bash
python -m src.presentation.cli.main_cli config
```

**Validate Configuration**:
```bash
python -m src.presentation.cli.main_cli config validate
```

**List Experiments**:
```bash
python -m src.presentation.cli.main_cli config experiments
```

## Troubleshooting

### Port Already in Use

**Problem**: Port 8000 is already in use.

**Solution 1 - Docker**:
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"
```

**Solution 2 - Non-Docker**:
```bash
# Set environment variable
export PORT=8001
poetry run uvicorn src.presentation.api:app --port 8001
```

### Import Errors

**Problem**: Import errors when running commands.

**Solution**:
```bash
# Reinstall dependencies
poetry install

# Verify Python path
poetry run python -c "import src"

# Check for missing packages
poetry show
```

### Storage Permission Errors

**Problem**: Cannot write to data directory.

**Solution**:
```bash
# Fix permissions
chmod -R 755 data/

# Or recreate directory
rm -rf data/
mkdir data
chmod 755 data
```

### Docker Build Issues

**Problem**: Docker build fails.

**Solution**:
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check Docker logs
docker-compose logs
```

### Health Check Failures

**Problem**: Health checks report unhealthy.

**Diagnosis**:
```bash
# Check API is running
curl http://localhost:8000/health/

# Check logs
docker-compose logs api

# Run validation
python -m scripts.maintenance.validate
```

### Model Endpoint Issues

**Problem**: Models are not responding.

**Diagnosis**:
```bash
# Check model health
curl http://localhost:8000/health/models

# Check local models (if using)
curl http://localhost:8000/chat
curl http://localhost:8001/chat
curl http://localhost:8002/chat
```

### Performance Issues

**Problem**: Application is slow.

**Check**:
```bash
# View system resources
docker stats ai-challenge-api

# Check metrics
python -m src.presentation.cli.main_cli metrics

# Check response times
curl http://localhost:8000/dashboard/data
```

## Maintenance Procedures

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
# Run all checks
./scripts/quality/run_all_checks.sh

# Check coverage
python -m scripts.quality.check_coverage

# Validate system
python -m scripts.maintenance.validate
```

**Update Dependencies**:
```bash
# Check for updates
poetry show --outdated

# Update dependencies
poetry update
```

### Backup and Restore

**Create Backup**:
```bash
# Automatic backup
make maintenance-backup

# Or manually
python -m scripts.maintenance.backup
```

**List Backups**:
```bash
python -m scripts.maintenance.backup --list
```

**Restore from Backup**:
```bash
python -m scripts.maintenance.backup --restore backups/backup_20240101.tar.gz
```

### Monitoring

**Metrics Dashboard**:
```
http://localhost:8000/dashboard/
```

**Metrics Export**:
```bash
# Export to JSON
python -m src.presentation.cli.main_cli metrics export json metrics.json

# Export metrics report
from src.infrastructure.monitoring.exporter import MetricsExporter
from src.infrastructure.monitoring.metrics import get_metrics

exporter = MetricsExporter(get_metrics())
exporter.export_to_markdown("report.md", include_history=True)
```

## FAQ

### General Questions

**Q: What is the recommended hardware configuration?**

A: For local development:
- CPU: 4+ cores
- RAM: 16GB+ (32GB for StarCoder)
- GPU: NVIDIA with 12GB+ VRAM (for StarCoder)
- Disk: 20GB+ (for models)

**Q: How do I add a new model?**

A: Add model configuration to `config/models.yaml`:

```yaml
models:
  my_model:
    base_url: http://localhost:8003
    max_tokens: 4096
    temperature: 0.7
```

**Q: How do I reset all metrics?**

A:
```bash
python -m src.presentation.cli.main_cli metrics reset
```

### Configuration Questions

**Q: How do I change the default model?**

A: Set environment variable:
```bash
export MODEL_NAME=mistral
```

Or in `docker-compose.yml`:
```yaml
environment:
  - MODEL_NAME=mistral
```

**Q: How do I adjust resource limits for Docker?**

A: Update `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
```

### Troubleshooting Questions

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

**Q: How do I view detailed logs?**

A:
```bash
# Docker
docker-compose logs -f api

# Non-Docker
# Check terminal output or set up logging to file
```

**Q: Why is the application slow?**

A: Check:
1. System resources (CPU, RAM, GPU)
2. Model response times
3. Network latency
4. Storage I/O

```bash
# Monitor resources
docker stats ai-challenge-api

# Check metrics
python -m src.presentation.cli.main_cli status
```

### Maintenance Questions

**Q: How often should I backup data?**

A: Recommended schedule:
- Daily for production
- Weekly for development
- Before major changes

```bash
# Use cron for automated backups
0 2 * * * cd /path/to/project && make maintenance-backup
```

**Q: How do I clean up old data?**

A:
```bash
# Preview (dry run)
python -m scripts.maintenance.cleanup --days 30 --dry-run

# Actually clean up
python -m scripts.maintenance.cleanup --days 30
```

**Q: What should I do if the application crashes?**

A: Steps:
1. Check logs: `docker-compose logs api`
2. Validate configuration: `python -m scripts.maintenance.validate`
3. Check health: `curl http://localhost:8000/health/`
4. Restart: `docker-compose restart api`
5. If persistent, restore from backup

## Additional Resources

- [Local Deployment Guide](./LOCAL_DEPLOYMENT.md)
- [API Documentation](http://localhost:8000/docs)
- [Health Dashboard](http://localhost:8000/dashboard/)
- CLI: `python -m src.presentation.cli.main_cli help`

## Support

For issues and questions:
1. Check logs and health status
2. Run validation: `python -m scripts.maintenance.validate`
3. Review documentation
4. Check GitHub issues

