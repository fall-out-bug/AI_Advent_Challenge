# Troubleshooting Guide

This guide provides solutions for common issues encountered when using the StarCoder Multi-Agent System.

## Table of Contents

- [Common Issues](#common-issues)
- [Debugging Steps](#debugging-steps)
- [Log Analysis](#log-analysis)
- [Performance Issues](#performance-issues)
- [Network Problems](#network-problems)
- [Model Issues](#model-issues)
- [Docker Issues](#docker-issues)
- [API Issues](#api-issues)
- [Error Codes](#error-codes)
- [Recovery Procedures](#recovery-procedures)

## Common Issues

### 1. Services Not Starting

#### Symptoms
- Docker containers fail to start
- Services return 503 errors
- Health checks fail

#### Causes
- Insufficient resources
- Port conflicts
- Configuration errors
- Missing dependencies

#### Solutions

**Check resource availability:**
```bash
# Check available memory
free -h

# Check available disk space
df -h

# Check CPU usage
top
```

**Check port conflicts:**
```bash
# Check if ports are in use
netstat -tulpn | grep :9001
netstat -tulpn | grep :9002
netstat -tulpn | grep :8003
```

**Verify configuration:**
```bash
# Check environment variables
cat .env

# Validate docker-compose file
docker-compose config
```

### 2. Model Connection Issues

#### Symptoms
- "Model not available" errors
- Timeout errors
- 500 Internal Server Error

#### Causes
- StarCoder service not running
- GPU not available
- Insufficient memory
- Network connectivity issues

#### Solutions

**Check StarCoder service:**
```bash
# Check if StarCoder is running
docker-compose ps starcoder

# Check StarCoder logs
docker-compose logs starcoder

# Test StarCoder health
curl http://localhost:8003/health
```

**Check GPU availability:**
```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

**Check memory usage:**
```bash
# Check GPU memory
nvidia-smi

# Check system memory
free -h
```

### 3. Code Generation Failures

#### Symptoms
- Empty responses
- Invalid code generation
- Parsing errors

#### Causes
- Model overload
- Invalid prompts
- Response parsing issues
- Token limits exceeded

#### Solutions

**Check model status:**
```bash
# Check model health
curl http://localhost:8003/health

# Check model logs
docker-compose logs starcoder
```

**Verify prompt format:**
```python
# Check prompt in code
from prompts.generator_prompts import GeneratorPrompts
prompts = GeneratorPrompts()
prompt = prompts.get_code_generation_prompt(
    task_description="test",
    language="python",
    requirements=""
)
print(prompt)
```

**Check token limits:**
```bash
# Check current token usage
curl http://localhost:9001/stats
```

### 4. Code Review Issues

#### Symptoms
- Review scores always 5.0
- Missing recommendations
- Parsing errors

#### Causes
- Model response format issues
- Prompt engineering problems
- JSON parsing failures

#### Solutions

**Check reviewer logs:**
```bash
# Check reviewer logs
docker-compose logs reviewer-agent
```

**Test review endpoint:**
```bash
# Test review endpoint
curl -X POST http://localhost:9002/review \
  -H "Content-Type: application/json" \
  -d '{"task_description": "test", "generated_code": "def test(): pass", "tests": "", "metadata": {}}'
```

**Verify prompt format:**
```python
# Check review prompt
from prompts.reviewer_prompts import ReviewerPrompts
prompts = ReviewerPrompts()
prompt = prompts.get_code_review_prompt(
    task_description="test",
    generated_code="def test(): pass",
    tests="",
    metadata={}
)
print(prompt)
```

## Debugging Steps

### 1. Systematic Debugging Approach

#### Step 1: Check Service Status
```bash
# Check all services
docker-compose ps

# Check service health
curl http://localhost:9001/health
curl http://localhost:9002/health
curl http://localhost:8003/health
```

#### Step 2: Check Logs
```bash
# Check recent logs
docker-compose logs --tail=50

# Check specific service logs
docker-compose logs generator-agent
docker-compose logs reviewer-agent
docker-compose logs starcoder
```

#### Step 3: Check Resources
```bash
# Check resource usage
docker stats

# Check system resources
free -h
df -h
nvidia-smi
```

#### Step 4: Test Connectivity
```bash
# Test internal connectivity
docker-compose exec generator-agent curl http://starcoder:8003/health
docker-compose exec reviewer-agent curl http://starcoder:8003/health
```

### 2. Debug Mode

#### Enable Debug Logging
```bash
# Set debug log level
export LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

#### Debug Script
Create `debug.sh`:
```bash
#!/bin/bash
set -euo pipefail

echo "🔍 Starting debug session..."

# Check system info
echo "📋 System Information:"
uname -a
docker --version
docker-compose --version

# Check services
echo "🐳 Docker Services:"
docker-compose ps

# Check logs
echo "📋 Recent Logs:"
docker-compose logs --tail=20

# Check resources
echo "💾 Resource Usage:"
docker stats --no-stream

# Test endpoints
echo "🌐 Testing Endpoints:"
curl -s http://localhost:9001/health || echo "❌ Generator unhealthy"
curl -s http://localhost:9002/health || echo "❌ Reviewer unhealthy"
curl -s http://localhost:8003/health || echo "❌ StarCoder unhealthy"

echo "✅ Debug session completed"
```

### 3. Interactive Debugging

#### Python Debugger
```python
import pdb; pdb.set_trace()
```

#### Docker Debugging
```bash
# Enter running container
docker-compose exec generator-agent bash

# Check container environment
docker-compose exec generator-agent env

# Check container processes
docker-compose exec generator-agent ps aux
```

## Log Analysis

### 1. Log Locations

#### Application Logs
- Generator Agent: `logs/generator.log`
- Reviewer Agent: `logs/reviewer.log`
- Orchestrator: `logs/orchestrator.log`

#### Docker Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs generator-agent
docker-compose logs reviewer-agent
docker-compose logs starcoder
```

#### System Logs
- Docker: `/var/log/docker.log`
- System: `/var/log/syslog`
- Kernel: `/var/log/kern.log`

### 2. Log Analysis Tools

#### Log Parser Script
Create `scripts/analyze-logs.sh`:
```bash
#!/bin/bash
set -euo pipefail

LOG_FILE="$1"

if [ -z "$LOG_FILE" ]; then
    echo "Usage: $0 <log_file>"
    exit 1
fi

echo "📊 Analyzing logs: $LOG_FILE"

# Count log levels
echo "📈 Log Level Distribution:"
grep -o '"level":"[^"]*"' "$LOG_FILE" | sort | uniq -c

# Count errors
echo "❌ Error Count:"
grep -c '"level":"ERROR"' "$LOG_FILE" || echo "0"

# Count warnings
echo "⚠️  Warning Count:"
grep -c '"level":"WARNING"' "$LOG_FILE" || echo "0"

# Most common errors
echo "🔍 Most Common Errors:"
grep '"level":"ERROR"' "$LOG_FILE" | grep -o '"message":"[^"]*"' | sort | uniq -c | head -10

# Performance metrics
echo "⏱️  Performance Metrics:"
grep '"workflow_time"' "$LOG_FILE" | grep -o '"workflow_time":[0-9.]*' | sort -n | tail -10
```

#### Log Monitoring
```bash
# Monitor logs in real-time
docker-compose logs -f

# Monitor specific service
docker-compose logs -f generator-agent

# Filter logs by level
docker-compose logs | grep ERROR
docker-compose logs | grep WARNING
```

### 3. Common Log Patterns

#### Error Patterns
```bash
# Connection errors
grep -i "connection" logs/*.log

# Timeout errors
grep -i "timeout" logs/*.log

# Memory errors
grep -i "memory" logs/*.log

# GPU errors
grep -i "cuda\|gpu" logs/*.log
```

#### Performance Patterns
```bash
# Slow requests
grep "workflow_time.*[5-9][0-9]" logs/*.log

# High token usage
grep "tokens_used.*[1-9][0-9][0-9][0-9]" logs/*.log
```

## Performance Issues

### 1. Slow Response Times

#### Symptoms
- Response times > 10 seconds
- Timeout errors
- High CPU usage

#### Diagnosis
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:9001/health

# Check CPU usage
docker stats --no-stream

# Check memory usage
free -h
```

#### Solutions

**Optimize model settings:**
```python
# Reduce max tokens
GENERATOR_MAX_TOKENS = 1000
REVIEWER_MAX_TOKENS = 800

# Adjust temperature
GENERATOR_TEMPERATURE = 0.2
REVIEWER_TEMPERATURE = 0.1
```

**Scale services:**
```bash
# Scale generator agent
docker-compose up -d --scale generator-agent=3

# Scale reviewer agent
docker-compose up -d --scale reviewer-agent=2
```

### 2. High Memory Usage

#### Symptoms
- Out of memory errors
- Slow performance
- System instability

#### Diagnosis
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check GPU memory
nvidia-smi
```

#### Solutions

**Optimize model memory:**
```python
# Use model quantization
MODEL_OPTIMIZATIONS = {
    "torch_dtype": "float16",
    "low_cpu_mem_usage": True,
    "device_map": "auto"
}
```

**Increase system memory:**
```bash
# Add swap space
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. High CPU Usage

#### Symptoms
- High CPU utilization
- Slow response times
- System overheating

#### Diagnosis
```bash
# Check CPU usage
top
htop

# Check per-container CPU usage
docker stats --no-stream
```

#### Solutions

**Optimize code:**
```python
# Use async/await properly
async def process_request(request):
    # Implementation
    pass

# Cache expensive operations
@lru_cache(maxsize=128)
def expensive_operation(param):
    # Implementation
    pass
```

**Scale services:**
```bash
# Scale services horizontally
docker-compose up -d --scale generator-agent=5
```

## Network Problems

### 1. Connection Issues

#### Symptoms
- Connection refused errors
- Timeout errors
- Service unavailable errors

#### Diagnosis
```bash
# Check network connectivity
ping localhost
ping starcoder
ping generator-agent
ping reviewer-agent

# Check port accessibility
telnet localhost 9001
telnet localhost 9002
telnet localhost 8003
```

#### Solutions

**Check Docker network:**
```bash
# List networks
docker network ls

# Inspect network
docker network inspect ai-challenge

# Recreate network
docker network rm ai-challenge
docker-compose up -d
```

**Check firewall:**
```bash
# Check firewall status
sudo ufw status

# Allow required ports
sudo ufw allow 9001
sudo ufw allow 9002
sudo ufw allow 8003
```

### 2. DNS Resolution Issues

#### Symptoms
- Name resolution failures
- Service discovery issues

#### Diagnosis
```bash
# Test DNS resolution
nslookup starcoder
nslookup generator-agent
nslookup reviewer-agent
```

#### Solutions

**Check Docker DNS:**
```bash
# Check DNS configuration
docker-compose exec generator-agent cat /etc/resolv.conf

# Restart services
docker-compose restart
```

### 3. Load Balancing Issues

#### Symptoms
- Uneven load distribution
- Some instances overloaded

#### Diagnosis
```bash
# Check Traefik configuration
curl http://localhost:8080/api/http/services

# Check service health
curl http://localhost:9001/health
curl http://localhost:9002/health
```

#### Solutions

**Optimize Traefik configuration:**
```yaml
# docker-compose.traefik.yml
services:
  traefik:
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--loadbalancer.healthcheck.interval=30s"
```

## Model Issues

### 1. StarCoder Specific Issues

#### Symptoms
- Model not loading
- CUDA errors
- Memory allocation failures

#### Diagnosis
```bash
# Check CUDA availability
nvidia-smi

# Check model logs
docker-compose logs starcoder

# Test model endpoint
curl http://localhost:8003/health
```

#### Solutions

**Check GPU requirements:**
```bash
# Verify GPU compatibility
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv

# Check CUDA version
nvcc --version
```

**Optimize model loading:**
```python
# Use model optimization
MODEL_CONFIG = {
    "torch_dtype": "float16",
    "device_map": "auto",
    "low_cpu_mem_usage": True,
    "use_cache": True
}
```

### 2. Model Response Issues

#### Symptoms
- Empty responses
- Invalid JSON
- Parsing errors

#### Diagnosis
```bash
# Test model directly
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "def hello():", "max_tokens": 100}'
```

#### Solutions

**Check prompt format:**
```python
# Verify prompt structure
prompt = f"""<fim_prefix>def hello():<fim_suffix><fim_middle>"""
```

**Handle response parsing:**
```python
try:
    response = await model_client.make_request(prompt)
    # Parse response
except Exception as e:
    logger.error(f"Model response parsing failed: {e}")
    # Fallback handling
```

### 3. Model Performance Issues

#### Symptoms
- Slow generation
- High memory usage
- Poor quality output

#### Solutions

**Optimize model parameters:**
```python
# Adjust generation parameters
GENERATION_PARAMS = {
    "temperature": 0.3,
    "max_tokens": 1000,
    "top_p": 0.9,
    "repetition_penalty": 1.1
}
```

**Use model quantization:**
```python
# Quantize model for better performance
MODEL_CONFIG = {
    "load_in_8bit": True,
    "device_map": "auto"
}
```

## Docker Issues

### 1. Container Startup Issues

#### Symptoms
- Containers fail to start
- Exit code 1
- Resource allocation failures

#### Diagnosis
```bash
# Check container status
docker-compose ps

# Check container logs
docker-compose logs

# Check Docker daemon
sudo systemctl status docker
```

#### Solutions

**Check resource limits:**
```bash
# Check available resources
free -h
df -h

# Adjust resource limits
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
    reservations:
      memory: 2G
```

**Check Docker configuration:**
```bash
# Check Docker daemon configuration
sudo cat /etc/docker/daemon.json

# Restart Docker daemon
sudo systemctl restart docker
```

### 2. Image Build Issues

#### Symptoms
- Build failures
- Dependency errors
- Permission issues

#### Diagnosis
```bash
# Check build logs
docker-compose build --no-cache

# Check Dockerfile syntax
docker build -t test .
```

#### Solutions

**Fix Dockerfile issues:**
```dockerfile
# Use specific base image
FROM python:3.10-slim

# Fix permissions
RUN chown -R appuser:appuser /app
USER appuser
```

**Clear Docker cache:**
```bash
# Clear build cache
docker builder prune -a

# Rebuild images
docker-compose build --no-cache
```

### 3. Volume Issues

#### Symptoms
- Permission denied errors
- Data not persisting
- Mount failures

#### Diagnosis
```bash
# Check volume mounts
docker-compose exec generator-agent ls -la /app

# Check volume permissions
docker volume ls
docker volume inspect <volume_name>
```

#### Solutions

**Fix volume permissions:**
```bash
# Create volume with proper permissions
docker volume create --driver local \
  --opt type=none \
  --opt device=/path/to/data \
  --opt o=bind,uid=1000,gid=1000 \
  starcoder-data
```

## API Issues

### 1. HTTP Errors

#### Symptoms
- 400 Bad Request
- 500 Internal Server Error
- 503 Service Unavailable

#### Diagnosis
```bash
# Test API endpoints
curl -v http://localhost:9001/health
curl -v http://localhost:9002/health

# Check API logs
docker-compose logs generator-agent
docker-compose logs reviewer-agent
```

#### Solutions

**Check request format:**
```bash
# Test with proper JSON
curl -X POST http://localhost:9001/generate \
  -H "Content-Type: application/json" \
  -d '{"task_description": "test", "language": "python", "requirements": ""}'
```

**Check API configuration:**
```python
# Verify API settings
app = FastAPI(
    title="Code Generator Agent",
    version="1.0.0",
    debug=False  # Set to False in production
)
```

### 2. Authentication Issues

#### Symptoms
- 401 Unauthorized
- 403 Forbidden
- Token validation errors

#### Solutions

**Check API keys:**
```bash
# Verify API key
curl -H "Authorization: Bearer $API_KEY" http://localhost:9001/health
```

**Check CORS configuration:**
```python
# Configure CORS properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Error Codes

### HTTP Status Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | OK | Success |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Check authentication |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check endpoint URL |
| 500 | Internal Server Error | Check server logs |
| 503 | Service Unavailable | Check service status |

### Application Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| MODEL_UNAVAILABLE | Model not available | Check StarCoder service |
| TIMEOUT_ERROR | Request timeout | Check network/performance |
| PARSING_ERROR | Response parsing failed | Check model response |
| VALIDATION_ERROR | Input validation failed | Check request data |
| MEMORY_ERROR | Out of memory | Check system resources |

## Recovery Procedures

### 1. Service Recovery

#### Restart Services
```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart generator-agent

# Force recreate services
docker-compose up -d --force-recreate
```

#### Rebuild Services
```bash
# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build generator-agent
```

### 2. Data Recovery

#### Restore from Backup
```bash
# Restore results
tar -xzf backup/results_20240115.tar.gz

# Restore configuration
tar -xzf backup/config_20240115.tar.gz
```

#### Reset to Clean State
```bash
# Stop all services
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up -d
```

### 3. System Recovery

#### Reset Docker
```bash
# Stop Docker
sudo systemctl stop docker

# Clean Docker
docker system prune -a

# Restart Docker
sudo systemctl start docker
```

#### Reset System
```bash
# Reboot system
sudo reboot

# Check system status
sudo systemctl status docker
sudo systemctl status nvidia-persistenced
```

## Getting Help

### 1. Self-Service Resources

- **Documentation**: Check this guide and other docs
- **Logs**: Analyze logs for error patterns
- **Health Checks**: Use provided health check scripts
- **Monitoring**: Check system metrics

### 2. Community Support

- **GitHub Issues**: Create detailed issue reports
- **Discord**: Join community discussions
- **Stack Overflow**: Search for similar issues

### 3. Professional Support

- **Enterprise Support**: Contact support team
- **Consulting**: Get professional assistance
- **Training**: Attend training sessions

### 4. Issue Reporting

When reporting issues, include:

1. **System Information**:
   - OS version
   - Docker version
   - GPU information
   - Available resources

2. **Error Details**:
   - Error messages
   - Stack traces
   - Log excerpts
   - Steps to reproduce

3. **Configuration**:
   - Environment variables
   - Docker Compose files
   - Custom configurations

4. **Attempted Solutions**:
   - What you've tried
   - What worked/didn't work
   - Expected vs actual behavior

## Conclusion

This troubleshooting guide provides comprehensive solutions for common issues in the StarCoder Multi-Agent System. Key principles:

1. **Systematic Approach**: Follow debugging steps in order
2. **Log Analysis**: Use logs to identify root causes
3. **Resource Monitoring**: Check system resources regularly
4. **Documentation**: Keep track of solutions for future reference
5. **Community**: Leverage community knowledge and support

For issues not covered in this guide, refer to the project documentation or create a detailed issue report.
