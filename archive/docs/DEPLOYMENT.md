# Deployment Documentation

## Overview

This document provides deployment instructions for the AI Challenge project.

## Local Development Setup

### Prerequisites

- Python 3.10+
- Poetry or pip
- Docker (optional)
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd AI_Challenge

# Install dependencies
pip install -r requirements.txt

# Or with Poetry
poetry install
```

### Environment Variables

```bash
# Copy example
cp api_key.txt.example api_key.txt

# Edit with your API key
nano api_key.txt
```

## Docker Deployment

### Building Image

```bash
# Build Docker image
docker build -t ai-challenge:latest .

# Or with docker-compose
docker-compose build
```

### Running Container

```bash
# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop container
docker-compose down
```

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEY=${API_KEY}
```

## Configuration Files

### Model Configuration

Edit `config/models.yml`:

```yaml
models:
  default: starcoder
  available:
    starcoder:
      max_input_tokens: 2048
      max_output_tokens: 1024
```

### Environment Variables

```bash
# .env file
API_KEY=your_api_key
MODEL_DEFAULT=starcoder
LOG_LEVEL=INFO
```

## Running the Application

### API Mode

```bash
# Run API server
python -m src.presentation.api

# Or with uvicorn
uvicorn src.presentation.api:app --reload
```

### CLI Mode

```bash
# Run CLI
python -m src.presentation.cli.main_cli generate "Create hello function"

# With arguments
python -m src.presentation.cli.main_cli review code.py
```

## Health Checks

### API Health Check

```bash
curl http://localhost:8000/health
```

### Service Status

```bash
# Check orchestrator status
python -m src.presentation.cli.main_cli status
```

## Monitoring

### Logs

```bash
# View application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f
```

### Metrics

The application tracks:
- Workflow execution time
- Token usage
- Success/failure rates
- Model performance metrics

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
```

### Load Balancing

Use Traefik or Nginx for load balancing:

```yaml
# traefik.yml
http:
  routers:
    ai-challenge:
      rule: "Host(`api.example.com`)"
      service: ai-challenge
```

## Production Deployment

### Security Considerations

1. **API Keys**: Store in secure vault
2. **HTTPS**: Enable SSL/TLS
3. **Authentication**: Implement API auth
4. **Rate Limiting**: Prevent abuse
5. **CORS**: Configure appropriately

### Environment-Specific Configs

```bash
# Development
export ENV=dev
export DEBUG=true

# Production
export ENV=prod
export DEBUG=false
```

## Troubleshooting

### Common Issues

#### Issue: Import Errors
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

#### Issue: Model Unavailable
```bash
# Solution: Check model configuration
cat config/models.yml
```

#### Issue: Port Already in Use
```bash
# Solution: Use different port
uvicorn src.presentation.api:app --port 8001
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debugger
python -m debugpy --listen 5678 src/presentation/api.py
```

## Backup and Recovery

### Data Backup

```bash
# Backup task storage
cp -r data/ backups/data-$(date +%Y%m%d)
```

### Configuration Backup

```bash
# Backup configurations
tar -czf config-backup.tar.gz config/
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest src/tests/
      - name: Check coverage
        run: pytest --cov=src --cov-report=term
```

## Performance Tuning

### Optimization Tips

1. **Async/Await**: Use throughout the application
2. **Connection Pooling**: Reuse database connections
3. **Caching**: Cache frequently accessed data
4. **Compression**: Enable gzip compression

### Resource Limits

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## Maintenance

### Regular Tasks

- Monitor logs for errors
- Check disk space usage
- Review performance metrics
- Update dependencies

### Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Pull latest code
git pull origin main
```

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review documentation in `docs/`
- Open an issue on GitHub

