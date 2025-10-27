# Руководство по развертыванию

[English](DEPLOYMENT.md) | [Русский](DEPLOYMENT.ru.md)

Это руководство предоставляет комплексные инструкции по развертыванию мульти-агентной системы StarCoder в различных окружениях.

## Содержание

- [Настройка продакшна](#настройка-продакшна)
- [Конфигурация окружения](#конфигурация-окружения)
- [Стратегии масштабирования](#стратегии-масштабирования)
- [Настройка мониторинга](#настройка-мониторинга)
- [Резервное копирование и восстановление](#резервное-копирование-и-восстановление)
- [Чеклист безопасности](#чеклист-безопасности)
- [Настройка производительности](#настройка-производительности)
- [Устранение неполадок](#устранение-неполадок)

## Настройка продакшна

### Предварительные требования

#### Требования к оборудованию

**Минимальные требования:**
- CPU: 8 cores
- RAM: 32GB
- GPU: NVIDIA RTX 4090 или эквивалент
- Storage: 500GB SSD
- Network: 1Gbps

**Рекомендуемые требования:**
- CPU: 16+ cores
- RAM: 64GB+
- GPU: NVIDIA A100 или эквивалент
- Storage: 1TB+ NVMe SSD
- Network: 10Gbps

#### Требования к программному обеспечению

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit
- Ubuntu 20.04+ или CentOS 8+
- Python 3.10+

### Шаги установки

#### 1. Подготовка системы

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Установка NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

#### 2. Клонирование и настройка

```bash
# Клонирование репозитория
git clone <repository-url>
cd AI_Challenge/day_07

# Создание файла окружения
cp .env.example .env
# Отредактируйте .env с продакшн значениями

# Создание необходимых директорий
mkdir -p logs results data
```

#### 3. Развертывание сервисов

```bash
# Запуск с Traefik (рекомендуется для продакшна)
make start-traefik

# Или запуск с bridge networking
make start-bridge
```

### Конфигурация продакшна

#### Docker Compose Production Override

Создайте `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  generator-agent:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - LOG_LEVEL=INFO
      - WORKERS=4
    volumes:
      - ./logs:/app/logs
      - ./results:/app/results

  reviewer-agent:
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - LOG_LEVEL=INFO
      - WORKERS=2
    volumes:
      - ./logs:/app/logs
      - ./results:/app/results

  traefik:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'
        reservations:
          memory: 256M
          cpus: '0.1'
```

#### Environment Configuration

```bash
# .env.prod
# Production environment variables

# Model Configuration
MODEL_NAME=starcoder
STARCODER_URL=http://starcoder:8000/chat
MISTRAL_URL=http://mistral:8001/chat
QWEN_URL=http://qwen:8002/chat
TINYLLAMA_URL=http://tinyllama:8003/chat

# HuggingFace Token
HF_TOKEN=your_production_huggingface_token

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance
WORKERS=4
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=300

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=generator.localhost,reviewer.localhost

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

## Конфигурация окружения

### Development Environment

```bash
# .env.dev
MODEL_NAME=starcoder
LOG_LEVEL=DEBUG
WORKERS=1
ENABLE_DEBUG=true
```

### Staging Environment

```bash
# .env.staging
MODEL_NAME=starcoder
LOG_LEVEL=INFO
WORKERS=2
ENABLE_METRICS=true
```

### Production Environment

```bash
# .env.prod
MODEL_NAME=starcoder
LOG_LEVEL=WARNING
WORKERS=4
ENABLE_METRICS=true
ENABLE_SECURITY=true
```

## Стратегии масштабирования

### Горизонтальное масштабирование

```bash
# Масштабирование агентов
docker-compose up -d --scale generator-agent=5 --scale reviewer-agent=3

# Проверка статуса
docker-compose ps
```

### Вертикальное масштабирование

```yaml
# docker-compose.scale.yml
services:
  generator-agent:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

### Load Balancing

```yaml
# Traefik load balancing configuration
services:
  generator-agent:
    labels:
      - "traefik.http.routers.generator.rule=Host(`generator.localhost`)"
      - "traefik.http.services.generator.loadbalancer.server.port=9001"
      - "traefik.http.services.generator.loadbalancer.sticky.cookie=true"
```

### Auto-scaling

```yaml
# docker-compose.autoscale.yml
services:
  generator-agent:
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 5s
```

## Настройка мониторинга

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'generator-agent'
    static_configs:
      - targets: ['generator-agent:9090']
  
  - job_name: 'reviewer-agent'
    static_configs:
      - targets: ['reviewer-agent:9090']
  
  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']
```

### Grafana Dashboard

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

### Health Checks

```python
# health_check.py
import asyncio
import httpx

async def check_health():
    """Check health of all services."""
    services = [
        "http://generator-agent:9001/health",
        "http://reviewer-agent:9002/health",
        "http://traefik:8080/ping"
    ]
    
    async with httpx.AsyncClient() as client:
        for service in services:
            try:
                response = await client.get(service, timeout=5.0)
                if response.status_code == 200:
                    print(f"✅ {service} is healthy")
                else:
                    print(f"❌ {service} returned {response.status_code}")
            except Exception as e:
                print(f"❌ {service} failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_health())
```

### Logging Configuration

```python
# logging_config.py
import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "INFO",
            "formatter": "json",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## Резервное копирование и восстановление

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Create backup directory
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration files
cp -r .env* "$BACKUP_DIR/"
cp -r docker-compose*.yml "$BACKUP_DIR/"

# Backup logs
cp -r logs/ "$BACKUP_DIR/"

# Backup results
cp -r results/ "$BACKUP_DIR/"

# Backup database (if applicable)
# pg_dump -h localhost -U postgres star_coder_db > "$BACKUP_DIR/database.sql"

# Compress backup
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

### Restore Strategy

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Extract backup
tar -xzf "$BACKUP_FILE"
BACKUP_DIR=$(basename "$BACKUP_FILE" .tar.gz)

# Restore configuration
cp -r "$BACKUP_DIR"/.env* .
cp -r "$BACKUP_DIR"/docker-compose*.yml .

# Restore logs
cp -r "$BACKUP_DIR"/logs .

# Restore results
cp -r "$BACKUP_DIR"/results .

# Restore database (if applicable)
# psql -h localhost -U postgres star_coder_db < "$BACKUP_DIR/database.sql"

# Cleanup
rm -rf "$BACKUP_DIR"

echo "Restore completed from: $BACKUP_FILE"
```

### Disaster Recovery

```bash
#!/bin/bash
# disaster_recovery.sh

# Stop all services
docker-compose down

# Remove all containers and volumes
docker system prune -a -f
docker volume prune -f

# Restore from latest backup
LATEST_BACKUP=$(ls -t /backups/*.tar.gz | head -n1)
./restore.sh "$LATEST_BACKUP"

# Start services
docker-compose up -d

# Verify health
./health_check.py
```

## Чеклист безопасности

### Pre-deployment Security Checklist

- [ ] **Environment Variables**
  - [ ] Все секреты в переменных окружения
  - [ ] Нет хардкода токенов в коде
  - [ ] Использование .env файлов

- [ ] **Docker Security**
  - [ ] Non-root пользователи в контейнерах
  - [ ] Multi-stage builds для минимального размера
  - [ ] Resource limits установлены
  - [ ] Health checks настроены

- [ ] **Network Security**
  - [ ] Firewall правила настроены
  - [ ] HTTPS используется для продакшна
  - [ ] Rate limiting включен
  - [ ] CORS настроен правильно

- [ ] **Application Security**
  - [ ] Валидация входных данных
  - [ ] Санитизация вывода
  - [ ] Логирование безопасности
  - [ ] Error handling без утечки информации

### Security Configuration

```yaml
# docker-compose.security.yml
services:
  generator-agent:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
    user: "1000:1000"
```

### Security Monitoring

```python
# security_monitor.py
import logging
import time
from collections import defaultdict

class SecurityMonitor:
    def __init__(self):
        self.request_counts = defaultdict(int)
        self.blocked_ips = set()
        self.logger = logging.getLogger('security')
    
    def check_rate_limit(self, ip_address: str) -> bool:
        """Check if IP is rate limited."""
        current_time = int(time.time())
        minute_key = f"{ip_address}:{current_time // 60}"
        
        self.request_counts[minute_key] += 1
        
        if self.request_counts[minute_key] > 100:  # 100 requests per minute
            self.blocked_ips.add(ip_address)
            self.logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return False
        
        return True
    
    def check_suspicious_patterns(self, request_data: dict) -> bool:
        """Check for suspicious request patterns."""
        # Check for SQL injection attempts
        suspicious_patterns = [
            "'; DROP TABLE",
            "UNION SELECT",
            "<script>",
            "eval(",
            "exec("
        ]
        
        request_str = str(request_data).lower()
        for pattern in suspicious_patterns:
            if pattern in request_str:
                self.logger.warning(f"Suspicious pattern detected: {pattern}")
                return False
        
        return True
```

## Настройка производительности

### Performance Tuning

```python
# performance_config.py
import os

# Async configuration
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '100'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '300'))

# Model configuration
MODEL_BATCH_SIZE = int(os.getenv('MODEL_BATCH_SIZE', '4'))
MODEL_CACHE_SIZE = int(os.getenv('MODEL_CACHE_SIZE', '100'))

# Worker configuration
WORKER_PROCESSES = int(os.getenv('WORKER_PROCESSES', '4'))
WORKER_THREADS = int(os.getenv('WORKER_THREADS', '8'))

# Memory configuration
MAX_MEMORY_USAGE = int(os.getenv('MAX_MEMORY_USAGE', '80'))  # 80% of available memory
```

### Caching Strategy

```python
# cache_config.py
import redis
from functools import wraps
import hashlib
import json

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_result(expiration=3600):
    """Cache function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(
                cache_key,
                expiration,
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator
```

### Database Optimization

```python
# database_config.py
import asyncio
import asyncpg

class DatabasePool:
    def __init__(self, connection_string: str, min_size: int = 10, max_size: int = 20):
        self.connection_string = connection_string
        self.min_size = min_size
        self.max_size = max_size
        self.pool = None
    
    async def initialize(self):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=60
        )
    
    async def execute_query(self, query: str, *args):
        """Execute query with connection pooling."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
```

## Устранение неполадок

### Common Issues

#### 1. Model Loading Issues

```bash
# Check GPU availability
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check model service logs
docker-compose logs starcoder-chat
```

#### 2. Memory Issues

```bash
# Check memory usage
docker stats

# Check system memory
free -h

# Monitor memory usage
htop
```

#### 3. Network Issues

```bash
# Check network connectivity
docker-compose exec generator-agent ping reviewer-agent

# Check port availability
netstat -tulpn | grep :9001

# Test API endpoints
curl http://localhost:9001/health
```

### Debugging Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f generator-agent

# Execute commands in container
docker-compose exec generator-agent bash

# Check container status
docker-compose ps

# Restart specific service
docker-compose restart generator-agent

# Scale services
docker-compose up -d --scale generator-agent=3
```

### Performance Debugging

```python
# performance_debug.py
import time
import psutil
import asyncio

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
    
    def log_request(self, duration: float, success: bool):
        """Log request performance."""
        self.request_count += 1
        if not success:
            self.error_count += 1
        
        # Log slow requests
        if duration > 10.0:  # 10 seconds
            print(f"Slow request detected: {duration:.2f}s")
    
    def get_stats(self):
        """Get performance statistics."""
        uptime = time.time() - self.start_time
        return {
            "uptime": uptime,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "requests_per_second": self.request_count / uptime,
            "memory_usage": psutil.virtual_memory().percent,
            "cpu_usage": psutil.cpu_percent()
        }
```

## Заключение

Это руководство предоставляет комплексные инструкции по развертыванию мульти-агентной системы StarCoder в различных окружениях. Следуйте этим инструкциям для обеспечения надежного, безопасного и производительного развертывания.

Ключевые моменты:
- **Правильная конфигурация**: Используйте соответствующие настройки для каждого окружения
- **Мониторинг**: Настройте комплексный мониторинг для отслеживания производительности
- **Безопасность**: Следуйте чеклисту безопасности для защиты системы
- **Масштабирование**: Планируйте масштабирование заранее
- **Резервное копирование**: Регулярно создавайте резервные копии

Для получения дополнительной информации обратитесь к:
- [Архитектурной документации](ARCHITECTURE.md)
- [Руководству разработчика](DEVELOPER_GUIDE.md)
- [Руководству по устранению неполадок](TROUBLESHOOTING.md)
