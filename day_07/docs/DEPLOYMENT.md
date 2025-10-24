# Deployment Guide

This guide provides comprehensive instructions for deploying the StarCoder Multi-Agent System in various environments.

## Table of Contents

- [Production Setup](#production-setup)
- [Environment Configuration](#environment-configuration)
- [Scaling Strategies](#scaling-strategies)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Recovery](#backup-and-recovery)
- [Security Checklist](#security-checklist)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## Production Setup

### Prerequisites

#### Hardware Requirements

**Minimum Requirements:**
- CPU: 8 cores
- RAM: 32GB
- GPU: NVIDIA RTX 4090 or equivalent
- Storage: 500GB SSD
- Network: 1Gbps

**Recommended Requirements:**
- CPU: 16+ cores
- RAM: 64GB+
- GPU: NVIDIA A100 or equivalent
- Storage: 1TB+ NVMe SSD
- Network: 10Gbps

#### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit
- Ubuntu 20.04+ or CentOS 8+
- Python 3.10+

### Installation Steps

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

#### 2. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd AI_Challenge/day_07

# Create environment file
cp .env.example .env
# Edit .env with production values

# Create necessary directories
mkdir -p logs results data
```

#### 3. Deploy Services

```bash
# Start with Traefik (recommended for production)
make start-traefik

# Or start with bridge networking
make start-bridge
```

### Production Configuration

#### Docker Compose Production Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  traefik:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  starcoder:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 32G
        reservations:
          cpus: '4'
          memory: 16G
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  generator-agent:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  reviewer-agent:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### Production Startup Script

Create `start-production.sh`:

```bash
#!/bin/bash
set -euo pipefail

echo "🚀 Starting StarCoder Multi-Agent System in Production Mode"

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Check GPU availability
if ! nvidia-smi >/dev/null 2>&1; then
    echo "⚠️  Warning: NVIDIA GPU not detected. StarCoder will not work properly."
fi

# Create necessary directories
mkdir -p logs results data

# Set production environment variables
export COMPOSE_PROJECT_NAME=starcoder-prod
export LOG_LEVEL=INFO
export DOCKER_BUILDKIT=1

# Start services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.traefik.yml -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo "🏥 Performing health checks..."
./scripts/health-check.sh

echo "✅ Production deployment completed!"
echo ""
echo "🌐 Access points:"
echo "   Generator API: http://generator.localhost"
echo "   Reviewer API:  http://reviewer.localhost"
echo "   Traefik Dashboard: http://localhost:8080"
```

## Environment Configuration

### Environment Variables

#### Required Variables

```bash
# HuggingFace Token (required for model access)
HF_TOKEN=your_huggingface_token_here

# Model Configuration
MODEL_NAME=starcoder
STARCODER_URL=http://starcoder:8003

# Agent URLs
GENERATOR_URL=http://generator-agent:9001
REVIEWER_URL=http://reviewer-agent:9002

# Logging
LOG_LEVEL=INFO
```

#### Optional Variables

```bash
# Performance Tuning
GENERATOR_MAX_TOKENS=1500
REVIEWER_MAX_TOKENS=1200
GENERATOR_TEMPERATURE=0.3
REVIEWER_TEMPERATURE=0.2

# Rate Limiting (disabled by default)
RATE_LIMIT_PER_MINUTE=60

# Health Check Configuration
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
HEALTH_CHECK_RETRIES=3

# File Paths
RESULTS_DIR=./results
LOGS_DIR=./logs
```

### Configuration Files

#### Traefik Configuration

Create `traefik.yml`:

```yaml
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: ai-challenge

log:
  level: INFO

accessLog:
  format: json
```

#### Logging Configuration

Create `logging.conf`:

```ini
[loggers]
keys=root,starcoder

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter,jsonFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_starcoder]
level=INFO
handlers=consoleHandler,fileHandler
qualname=starcoder
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=jsonFormatter
args=('logs/starcoder.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_jsonFormatter]
format={"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}
```

## Scaling Strategies

### Horizontal Scaling

#### Load Balancer Configuration

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  generator-agent:
    deploy:
      replicas: 5
      update_config:
        parallelism: 2
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  reviewer-agent:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

#### Auto-scaling Script

Create `scripts/auto-scale.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Configuration
MIN_REPLICAS=2
MAX_REPLICAS=10
SCALE_UP_THRESHOLD=80
SCALE_DOWN_THRESHOLD=20
CHECK_INTERVAL=60

while true; do
    # Get current CPU usage
    CPU_USAGE=$(docker stats --no-stream --format "table {{.CPUPerc}}" | tail -n +2 | awk '{print $1}' | sed 's/%//' | awk '{sum+=$1} END {print sum/NR}')
    
    # Get current replica count
    CURRENT_REPLICAS=$(docker-compose ps generator-agent | grep -c "Up")
    
    echo "Current CPU usage: ${CPU_USAGE}%, Current replicas: ${CURRENT_REPLICAS}"
    
    if (( $(echo "$CPU_USAGE > $SCALE_UP_THRESHOLD" | bc -l) )) && [ "$CURRENT_REPLICAS" -lt "$MAX_REPLICAS" ]; then
        echo "Scaling up generator-agent..."
        docker-compose up -d --scale generator-agent=$((CURRENT_REPLICAS + 1))
    elif (( $(echo "$CPU_USAGE < $SCALE_DOWN_THRESHOLD" | bc -l) )) && [ "$CURRENT_REPLICAS" -gt "$MIN_REPLICAS" ]; then
        echo "Scaling down generator-agent..."
        docker-compose up -d --scale generator-agent=$((CURRENT_REPLICAS - 1))
    fi
    
    sleep $CHECK_INTERVAL
done
```

### Vertical Scaling

#### Resource Optimization

```yaml
# docker-compose.vertical.yml
version: '3.8'

services:
  starcoder:
    deploy:
      resources:
        limits:
          cpus: '16'
          memory: 64G
        reservations:
          cpus: '8'
          memory: 32G

  generator-agent:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Database Scaling

#### Redis Cache Setup

```yaml
# docker-compose.cache.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: redis-cache
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

volumes:
  redis-data:
```

## Monitoring Setup

### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']
    metrics_path: '/metrics'

  - job_name: 'generator-agent'
    static_configs:
      - targets: ['generator-agent:9001']
    metrics_path: '/metrics'

  - job_name: 'reviewer-agent'
    static_configs:
      - targets: ['reviewer-agent:9002']
    metrics_path: '/metrics'

  - job_name: 'starcoder'
    static_configs:
      - targets: ['starcoder:8003']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Create `monitoring/grafana/dashboards/starcoder.json`:

```json
{
  "dashboard": {
    "title": "StarCoder Multi-Agent System",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

Create `monitoring/rules/alerts.yml`:

```yaml
groups:
  - name: starcoder_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "{{ $labels.instance }} is down"
```

## Backup and Recovery

### Data Backup Strategy

#### Automated Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="starcoder_backup_${DATE}.tar.gz"

echo "🔄 Starting backup process..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup results directory
echo "📁 Backing up results..."
tar -czf "$BACKUP_DIR/results_${DATE}.tar.gz" results/

# Backup logs directory
echo "📋 Backing up logs..."
tar -czf "$BACKUP_DIR/logs_${DATE}.tar.gz" logs/

# Backup configuration files
echo "⚙️  Backing up configuration..."
tar -czf "$BACKUP_DIR/config_${DATE}.tar.gz" .env docker-compose*.yml

# Create full backup
echo "📦 Creating full backup..."
tar -czf "$BACKUP_DIR/$BACKUP_FILE" results/ logs/ .env docker-compose*.yml

# Upload to cloud storage (optional)
if [ -n "${AWS_S3_BUCKET:-}" ]; then
    echo "☁️  Uploading to S3..."
    aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" "s3://$AWS_S3_BUCKET/backups/"
fi

# Cleanup old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "starcoder_backup_*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed: $BACKUP_FILE"
```

#### Cron Job Setup

```bash
# Add to crontab
0 2 * * * /path/to/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Recovery Procedures

#### Data Recovery Script

Create `scripts/restore.sh`:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Starting restore process..."

# Stop services
echo "🛑 Stopping services..."
docker-compose down

# Extract backup
echo "📦 Extracting backup..."
tar -xzf "$BACKUP_FILE"

# Restart services
echo "🚀 Restarting services..."
docker-compose up -d

echo "✅ Restore completed"
```

## Security Checklist

### Pre-deployment Security

- [ ] **System Updates**: All packages updated
- [ ] **Firewall**: Configured and enabled
- [ ] **SSH**: Key-based authentication only
- [ ] **Users**: Non-root users created
- [ ] **Docker**: Security scanning enabled
- [ ] **Secrets**: Environment variables secured
- [ ] **Network**: Proper segmentation
- [ ] **Monitoring**: Security monitoring enabled

### Runtime Security

- [ ] **Containers**: Running as non-root
- [ ] **Images**: Minimal base images
- [ ] **Networks**: Isolated networks
- [ ] **Volumes**: Proper permissions
- [ ] **Logs**: Security events logged
- [ ] **Updates**: Regular security updates
- [ ] **Access**: Limited access controls
- [ ] **Encryption**: Data encrypted

### Security Hardening Script

Create `scripts/security-harden.sh`:

```bash
#!/bin/bash
set -euo pipefail

echo "🔒 Starting security hardening..."

# Update system
apt update && apt upgrade -y

# Install security tools
apt install -y ufw fail2ban unattended-upgrades

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Configure automatic updates
cat > /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
EOF

echo "✅ Security hardening completed"
```

## Performance Tuning

### System Optimization

#### Kernel Parameters

```bash
# /etc/sysctl.conf
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr
```

#### Docker Optimization

```bash
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "default-ulimits": {
    "nofile": {
      "Hard": 64000,
      "Name": "nofile",
      "Soft": 64000
    }
  }
}
```

### Application Optimization

#### Model Optimization

```python
# Model-specific optimizations
MODEL_OPTIMIZATIONS = {
    "starcoder": {
        "torch_dtype": "float16",
        "device_map": "auto",
        "low_cpu_mem_usage": True,
        "use_cache": True
    },
    "mistral": {
        "torch_dtype": "float16",
        "device_map": "auto",
        "low_cpu_mem_usage": True
    }
}
```

#### Caching Strategy

```python
# Redis caching implementation
import redis
import json

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
    
    def get(self, key):
        value = self.redis_client.get(key)
        return json.loads(value) if value else None
    
    def set(self, key, value, ttl=3600):
        self.redis_client.setex(key, ttl, json.dumps(value))
```

## Troubleshooting

### Common Issues

#### 1. GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Restart Docker
sudo systemctl restart docker
```

#### 2. Memory Issues

```bash
# Check memory usage
free -h
docker stats

# Increase swap if needed
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. Network Issues

```bash
# Check network connectivity
docker network ls
docker network inspect ai-challenge

# Test service connectivity
curl http://localhost:9001/health
curl http://localhost:9002/health
```

### Debugging Tools

#### Health Check Script

Create `scripts/health-check.sh`:

```bash
#!/bin/bash
set -euo pipefail

echo "🏥 Performing health checks..."

# Check Docker services
echo "🐳 Checking Docker services..."
docker-compose ps

# Check service health
echo "🔍 Checking service health..."
curl -f http://localhost:9001/health || echo "❌ Generator agent unhealthy"
curl -f http://localhost:9002/health || echo "❌ Reviewer agent unhealthy"

# Check logs for errors
echo "📋 Checking logs for errors..."
docker-compose logs --tail=50 | grep -i error || echo "✅ No errors found"

echo "✅ Health check completed"
```

#### Performance Monitoring

Create `scripts/performance-monitor.sh`:

```bash
#!/bin/bash
set -euo pipefail

echo "📊 Performance monitoring..."

# CPU usage
echo "🖥️  CPU Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Disk usage
echo "💾 Disk Usage:"
df -h

# Network usage
echo "🌐 Network Usage:"
docker network ls
docker network inspect ai-challenge | grep -A 10 "Containers"

echo "✅ Performance monitoring completed"
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying the StarCoder Multi-Agent System in production environments. Key considerations:

1. **Scalability**: Horizontal and vertical scaling strategies
2. **Monitoring**: Comprehensive monitoring and alerting
3. **Security**: Security hardening and best practices
4. **Backup**: Automated backup and recovery procedures
5. **Performance**: Optimization techniques and tuning

Follow these guidelines to ensure a robust, secure, and performant deployment of the StarCoder Multi-Agent System.
