# Руководство по устранению неполадок

[English](TROUBLESHOOTING.md) | [Русский](TROUBLESHOOTING.ru.md)

Это руководство предоставляет решения для частых проблем, возникающих при использовании мульти-агентной системы StarCoder.

## Содержание

- [Частые проблемы](#частые-проблемы)
- [Шаги отладки](#шаги-отладки)
- [Анализ логов](#анализ-логов)
- [Проблемы производительности](#проблемы-производительности)
- [Сетевые проблемы](#сетевые-проблемы)
- [Проблемы с моделями](#проблемы-с-моделями)
- [Проблемы Docker](#проблемы-docker)
- [Проблемы API](#проблемы-api)
- [Коды ошибок](#коды-ошибок)
- [Процедуры восстановления](#процедуры-восстановления)

## Частые проблемы

### 1. Сервисы не запускаются

#### Симптомы
- Docker контейнеры не запускаются
- Сервисы возвращают ошибки 503
- Health checks не проходят

#### Причины
- Недостаточно ресурсов
- Конфликты портов
- Ошибки конфигурации
- Отсутствующие зависимости

#### Решения

**Проверка доступности ресурсов:**
```bash
# Проверка доступной памяти
free -h

# Проверка свободного места на диске
df -h

# Проверка использования CPU
top
```

**Проверка конфликтов портов:**
```bash
# Проверка использования портов
netstat -tulpn | grep :9001
netstat -tulpn | grep :9002
netstat -tulpn | grep :8003
```

**Проверка конфигурации:**
```bash
# Проверка переменных окружения
cat .env

# Валидация docker-compose файла
docker-compose config
```

### 2. Проблемы подключения к моделям

#### Симптомы
- Ошибки "Model not available"
- Ошибки таймаута
- 500 Internal Server Error

#### Причины
- Сервис StarCoder не запущен
- GPU недоступен
- Недостаточно памяти
- Проблемы сетевого подключения

#### Решения

**Проверка сервиса StarCoder:**
```bash
# Проверка запуска StarCoder
docker-compose ps starcoder

# Проверка логов StarCoder
docker-compose logs starcoder

# Тест здоровья StarCoder
curl http://localhost:8003/health
```

**Проверка доступности GPU:**
```bash
# Проверка NVIDIA драйвера
nvidia-smi

# Проверка поддержки GPU в Docker
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

**Проверка использования памяти:**
```bash
# Проверка использования памяти контейнерами
docker stats

# Проверка системной памяти
free -h

# Мониторинг памяти в реальном времени
htop
```

### 3. Медленная генерация кода

#### Симптомы
- Время генерации > 30 секунд
- Таймауты запросов
- Высокое использование CPU/GPU

#### Причины
- Недостаточно GPU памяти
- Медленная модель
- Высокая нагрузка на систему
- Неоптимальные настройки модели

#### Решения

**Оптимизация GPU:**
```bash
# Проверка использования GPU
nvidia-smi

# Очистка GPU памяти
sudo fuser -v /dev/nvidia*

# Перезапуск сервисов для освобождения памяти
docker-compose restart
```

**Выбор более быстрой модели:**
```bash
# Использование TinyLlama для быстрых ответов
export MODEL_NAME=tinyllama

# Использование Qwen для баланса скорости и качества
export MODEL_NAME=qwen
```

**Оптимизация настроек:**
```python
# Уменьшение max_tokens для более быстрых ответов
MODEL_SPECIFIC_SETTINGS = {
    "starcoder": {
        "generator_max_tokens": 800,  # Уменьшено с 1500
        "reviewer_max_tokens": 600   # Уменьшено с 1200
    }
}
```

### 4. Ошибки валидации кода

#### Симптомы
- "Invalid code generated" ошибки
- Синтаксические ошибки в сгенерированном коде
- Проблемы с импортами

#### Причины
- Неправильные промпты
- Ограничения модели
- Проблемы с парсингом ответа

#### Решения

**Улучшение промптов:**
```python
# Более конкретные промпты
def create_detailed_prompt(task_description: str) -> str:
    return f"""
    Create a Python function that:
    1. Has a clear docstring
    2. Includes type hints
    3. Has proper error handling
    4. Follows PEP 8 style
    
    Task: {task_description}
    
    Return only the function code, no explanations.
    """
```

**Улучшение валидации:**
```python
import ast

def validate_python_code(code: str) -> bool:
    """Validate Python code syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        return False
```

## Шаги отладки

### 1. Системная диагностика

```bash
#!/bin/bash
# system_diagnostics.sh

echo "=== System Diagnostics ==="

# Check system resources
echo "Memory usage:"
free -h

echo "Disk usage:"
df -h

echo "CPU usage:"
top -bn1 | grep "Cpu(s)"

# Check Docker status
echo "Docker status:"
docker --version
docker-compose --version

# Check GPU status
echo "GPU status:"
nvidia-smi || echo "NVIDIA driver not available"

# Check network
echo "Network status:"
ping -c 3 8.8.8.8
```

### 2. Контейнерная диагностика

```bash
#!/bin/bash
# container_diagnostics.sh

echo "=== Container Diagnostics ==="

# Check container status
echo "Container status:"
docker-compose ps

# Check container logs
echo "Generator agent logs:"
docker-compose logs --tail=50 generator-agent

echo "Reviewer agent logs:"
docker-compose logs --tail=50 reviewer-agent

# Check container resources
echo "Container resource usage:"
docker stats --no-stream

# Check container health
echo "Health checks:"
curl -s http://localhost:9001/health || echo "Generator agent not responding"
curl -s http://localhost:9002/health || echo "Reviewer agent not responding"
```

### 3. API диагностика

```bash
#!/bin/bash
# api_diagnostics.sh

echo "=== API Diagnostics ==="

# Test generator API
echo "Testing generator API:"
curl -X POST http://localhost:9001/generate \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Create a simple hello world function"}' \
  -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n"

# Test reviewer API
echo "Testing reviewer API:"
curl -X POST http://localhost:9002/review \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): return \"Hello World\"", "tests": "def test_hello(): assert hello() == \"Hello World\""}' \
  -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n"

# Test model connectivity
echo "Testing model connectivity:"
curl -s http://localhost:8003/health || echo "StarCoder model not responding"
```

## Анализ логов

### 1. Структурированные логи

```python
# log_analyzer.py
import json
import re
from collections import defaultdict
from datetime import datetime

class LogAnalyzer:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.errors = defaultdict(int)
        self.warnings = defaultdict(int)
        self.performance_issues = []
    
    def analyze_logs(self):
        """Analyze log file for issues."""
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    self._process_log_entry(log_entry)
                except json.JSONDecodeError:
                    # Handle non-JSON logs
                    self._process_text_log(line)
    
    def _process_log_entry(self, entry: dict):
        """Process structured log entry."""
        level = entry.get('level', '').upper()
        message = entry.get('message', '')
        
        if level == 'ERROR':
            self.errors[message] += 1
        elif level == 'WARNING':
            self.warnings[message] += 1
        
        # Check for performance issues
        if 'duration' in entry and entry['duration'] > 10.0:
            self.performance_issues.append(entry)
    
    def _process_text_log(self, line: str):
        """Process text log line."""
        if 'ERROR' in line:
            error_match = re.search(r'ERROR: (.+)', line)
            if error_match:
                self.errors[error_match.group(1)] += 1
        
        if 'WARNING' in line:
            warning_match = re.search(r'WARNING: (.+)', line)
            if warning_match:
                self.warnings[warning_match.group(1)] += 1
    
    def get_report(self):
        """Generate analysis report."""
        report = {
            "total_errors": sum(self.errors.values()),
            "total_warnings": sum(self.warnings.values()),
            "top_errors": dict(sorted(self.errors.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_warnings": dict(sorted(self.warnings.items(), key=lambda x: x[1], reverse=True)[:5]),
            "performance_issues": len(self.performance_issues)
        }
        return report

# Usage
analyzer = LogAnalyzer('logs/app.log')
analyzer.analyze_logs()
report = analyzer.get_report()
print(json.dumps(report, indent=2))
```

### 2. Мониторинг в реальном времени

```bash
#!/bin/bash
# real_time_monitoring.sh

echo "Starting real-time monitoring..."

# Monitor logs for errors
docker-compose logs -f | grep --line-buffered "ERROR" | while read line; do
    echo "[$(date)] ERROR detected: $line"
    # Send alert or notification
done &

# Monitor system resources
while true; do
    echo "[$(date)] Memory usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo "[$(date)] CPU usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    sleep 30
done
```

## Проблемы производительности

### 1. Медленные запросы

```python
# performance_monitor.py
import time
import asyncio
from functools import wraps

class PerformanceMonitor:
    def __init__(self):
        self.request_times = []
        self.slow_requests = []
    
    def monitor_request(self, threshold: float = 5.0):
        """Decorator to monitor request performance."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    self.request_times.append(duration)
                    
                    if duration > threshold:
                        self.slow_requests.append({
                            'function': func.__name__,
                            'duration': duration,
                            'timestamp': time.time()
                        })
                        print(f"Slow request detected: {func.__name__} took {duration:.2f}s")
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    print(f"Request failed after {duration:.2f}s: {e}")
                    raise
            return wrapper
        return decorator
    
    def get_stats(self):
        """Get performance statistics."""
        if not self.request_times:
            return {}
        
        return {
            'total_requests': len(self.request_times),
            'average_time': sum(self.request_times) / len(self.request_times),
            'max_time': max(self.request_times),
            'min_time': min(self.request_times),
            'slow_requests': len(self.slow_requests)
        }

# Usage
monitor = PerformanceMonitor()

@monitor.monitor_request(threshold=3.0)
async def generate_code(task_description: str):
    # Code generation logic
    pass
```

### 2. Оптимизация памяти

```python
# memory_optimizer.py
import gc
import psutil
import asyncio

class MemoryOptimizer:
    def __init__(self, max_memory_percent: float = 80.0):
        self.max_memory_percent = max_memory_percent
        self.memory_warnings = 0
    
    def check_memory_usage(self):
        """Check current memory usage."""
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.max_memory_percent:
            self.memory_warnings += 1
            print(f"High memory usage: {memory_percent:.1f}%")
            return False
        return True
    
    def optimize_memory(self):
        """Optimize memory usage."""
        # Force garbage collection
        gc.collect()
        
        # Clear caches if available
        if hasattr(self, 'cache'):
            self.cache.clear()
        
        print("Memory optimization completed")
    
    async def monitor_memory(self):
        """Continuously monitor memory usage."""
        while True:
            if not self.check_memory_usage():
                self.optimize_memory()
            
            await asyncio.sleep(60)  # Check every minute

# Usage
optimizer = MemoryOptimizer()
asyncio.create_task(optimizer.monitor_memory())
```

## Сетевые проблемы

### 1. Проблемы подключения

```bash
#!/bin/bash
# network_troubleshooting.sh

echo "=== Network Troubleshooting ==="

# Check basic connectivity
echo "Testing basic connectivity:"
ping -c 3 8.8.8.8

# Check DNS resolution
echo "Testing DNS resolution:"
nslookup google.com

# Check local network
echo "Testing local network:"
ping -c 3 $(hostname -I | awk '{print $1}')

# Check Docker network
echo "Testing Docker network:"
docker network ls
docker network inspect day_07_default

# Check port accessibility
echo "Testing port accessibility:"
for port in 9001 9002 8003; do
    if nc -z localhost $port; then
        echo "Port $port is accessible"
    else
        echo "Port $port is not accessible"
    fi
done
```

### 2. Проблемы меж-агентной коммуникации

```python
# communication_tester.py
import asyncio
import httpx
import time

class CommunicationTester:
    def __init__(self):
        self.generator_url = "http://generator-agent:9001"
        self.reviewer_url = "http://reviewer-agent:9002"
        self.timeout = 30.0
    
    async def test_generator_connectivity(self):
        """Test generator agent connectivity."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.generator_url}/health")
                if response.status_code == 200:
                    print("✅ Generator agent is reachable")
                    return True
                else:
                    print(f"❌ Generator agent returned {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Generator agent connectivity failed: {e}")
            return False
    
    async def test_reviewer_connectivity(self):
        """Test reviewer agent connectivity."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.reviewer_url}/health")
                if response.status_code == 200:
                    print("✅ Reviewer agent is reachable")
                    return True
                else:
                    print(f"❌ Reviewer agent returned {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Reviewer agent connectivity failed: {e}")
            return False
    
    async def test_inter_agent_communication(self):
        """Test communication between agents."""
        try:
            # Generate code
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                generate_response = await client.post(
                    f"{self.generator_url}/generate",
                    json={"task_description": "Create a simple function"}
                )
                
                if generate_response.status_code != 200:
                    print("❌ Code generation failed")
                    return False
                
                generated_data = generate_response.json()
                
                # Review code
                review_response = await client.post(
                    f"{self.reviewer_url}/review",
                    json={
                        "code": generated_data.get("code", ""),
                        "tests": generated_data.get("tests", "")
                    }
                )
                
                if review_response.status_code == 200:
                    print("✅ Inter-agent communication successful")
                    return True
                else:
                    print("❌ Code review failed")
                    return False
                    
        except Exception as e:
            print(f"❌ Inter-agent communication failed: {e}")
            return False

# Usage
async def main():
    tester = CommunicationTester()
    
    print("Testing agent connectivity...")
    generator_ok = await tester.test_generator_connectivity()
    reviewer_ok = await tester.test_reviewer_connectivity()
    
    if generator_ok and reviewer_ok:
        print("Testing inter-agent communication...")
        await tester.test_inter_agent_communication()

asyncio.run(main())
```

## Проблемы с моделями

### 1. Проблемы загрузки модели

```bash
#!/bin/bash
# model_troubleshooting.sh

echo "=== Model Troubleshooting ==="

# Check StarCoder service
echo "Checking StarCoder service:"
docker-compose ps starcoder-chat

# Check StarCoder logs
echo "StarCoder logs (last 50 lines):"
docker-compose logs --tail=50 starcoder-chat

# Check GPU availability
echo "GPU availability:"
nvidia-smi

# Check model health
echo "Model health check:"
curl -s http://localhost:8003/health | jq . || echo "Model health check failed"

# Test model response
echo "Testing model response:"
curl -X POST http://localhost:8003/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, are you working?"}' \
  -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n"
```

### 2. Проблемы качества генерации

```python
# quality_monitor.py
import re
import ast
from typing import List, Dict

class QualityMonitor:
    def __init__(self):
        self.quality_issues = []
    
    def check_code_quality(self, code: str) -> Dict[str, List[str]]:
        """Check code quality and return issues."""
        issues = {
            'syntax_errors': [],
            'style_issues': [],
            'logic_issues': [],
            'security_issues': []
        }
        
        # Check syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues['syntax_errors'].append(f"Syntax error: {e}")
        
        # Check style issues
        if not self._has_docstring(code):
            issues['style_issues'].append("Missing docstring")
        
        if not self._has_type_hints(code):
            issues['style_issues'].append("Missing type hints")
        
        # Check security issues
        dangerous_patterns = [
            r'eval\(',
            r'exec\(',
            r'__import__\(',
            r'os\.system\(',
            r'subprocess\.'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                issues['security_issues'].append(f"Dangerous pattern detected: {pattern}")
        
        return issues
    
    def _has_docstring(self, code: str) -> bool:
        """Check if code has docstring."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if ast.get_docstring(node):
                        return True
        except:
            pass
        return False
    
    def _has_type_hints(self, code: str) -> bool:
        """Check if code has type hints."""
        return ':' in code and '->' in code
    
    def generate_quality_report(self, code: str) -> str:
        """Generate quality report for code."""
        issues = self.check_code_quality(code)
        
        report = "Code Quality Report:\n"
        report += "=" * 50 + "\n"
        
        for category, issue_list in issues.items():
            if issue_list:
                report += f"\n{category.replace('_', ' ').title()}:\n"
                for issue in issue_list:
                    report += f"  - {issue}\n"
        
        if not any(issues.values()):
            report += "\n✅ No quality issues detected!"
        
        return report

# Usage
monitor = QualityMonitor()
code = """
def hello_world():
    return "Hello, World!"
"""
report = monitor.generate_quality_report(code)
print(report)
```

## Проблемы Docker

### 1. Проблемы контейнеров

```bash
#!/bin/bash
# docker_troubleshooting.sh

echo "=== Docker Troubleshooting ==="

# Check Docker daemon
echo "Docker daemon status:"
systemctl status docker

# Check Docker version
echo "Docker version:"
docker --version
docker-compose --version

# Check container status
echo "Container status:"
docker-compose ps

# Check container logs
echo "Container logs:"
docker-compose logs --tail=20

# Check container resources
echo "Container resource usage:"
docker stats --no-stream

# Check Docker images
echo "Docker images:"
docker images

# Check Docker volumes
echo "Docker volumes:"
docker volume ls

# Check Docker networks
echo "Docker networks:"
docker network ls
```

### 2. Проблемы сборки

```bash
#!/bin/bash
# build_troubleshooting.sh

echo "=== Build Troubleshooting ==="

# Clean Docker cache
echo "Cleaning Docker cache:"
docker system prune -f
docker builder prune -f

# Rebuild without cache
echo "Rebuilding without cache:"
docker-compose build --no-cache

# Check build logs
echo "Build logs:"
docker-compose build 2>&1 | tee build.log

# Check for build errors
echo "Checking for build errors:"
grep -i "error\|failed" build.log || echo "No build errors found"
```

## Проблемы API

### 1. Проблемы endpoints

```python
# api_tester.py
import asyncio
import httpx
import json

class APITester:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.generator_url = f"{base_url}:9001"
        self.reviewer_url = f"{base_url}:9002"
    
    async def test_all_endpoints(self):
        """Test all API endpoints."""
        tests = [
            ("Generator Health", self._test_generator_health),
            ("Reviewer Health", self._test_reviewer_health),
            ("Generator Generate", self._test_generator_generate),
            ("Reviewer Review", self._test_reviewer_review),
            ("Generator Stats", self._test_generator_stats),
            ("Reviewer Stats", self._test_reviewer_stats)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = {"status": "PASS", "result": result}
                print(f"✅ {test_name}: PASS")
            except Exception as e:
                results[test_name] = {"status": "FAIL", "error": str(e)}
                print(f"❌ {test_name}: FAIL - {e}")
        
        return results
    
    async def _test_generator_health(self):
        """Test generator health endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.generator_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def _test_reviewer_health(self):
        """Test reviewer health endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.reviewer_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def _test_generator_generate(self):
        """Test generator generate endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.generator_url}/generate",
                json={"task_description": "Create a simple hello world function"}
            )
            response.raise_for_status()
            return response.json()
    
    async def _test_reviewer_review(self):
        """Test reviewer review endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.reviewer_url}/review",
                json={
                    "code": "def hello(): return 'Hello World'",
                    "tests": "def test_hello(): assert hello() == 'Hello World'"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def _test_generator_stats(self):
        """Test generator stats endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.generator_url}/stats")
            response.raise_for_status()
            return response.json()
    
    async def _test_reviewer_stats(self):
        """Test reviewer stats endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.reviewer_url}/stats")
            response.raise_for_status()
            return response.json()

# Usage
async def main():
    tester = APITester()
    results = await tester.test_all_endpoints()
    
    print("\nTest Results Summary:")
    print("=" * 50)
    for test_name, result in results.items():
        status = result["status"]
        print(f"{test_name}: {status}")

asyncio.run(main())
```

## Коды ошибок

### 1. HTTP коды ошибок

| Код | Описание | Причина | Решение |
|-----|----------|---------|---------|
| 400 | Bad Request | Неправильный формат запроса | Проверить JSON формат |
| 401 | Unauthorized | Отсутствует токен аутентификации | Добавить токен в заголовки |
| 403 | Forbidden | Недостаточно прав доступа | Проверить права пользователя |
| 404 | Not Found | Endpoint не найден | Проверить URL |
| 408 | Request Timeout | Превышен таймаут запроса | Увеличить таймаут |
| 429 | Too Many Requests | Превышен лимит запросов | Подождать или увеличить лимит |
| 500 | Internal Server Error | Внутренняя ошибка сервера | Проверить логи сервера |
| 502 | Bad Gateway | Проблема с upstream сервером | Проверить доступность модели |
| 503 | Service Unavailable | Сервис недоступен | Проверить статус контейнеров |
| 504 | Gateway Timeout | Таймаут gateway | Проверить производительность |

### 2. Коды ошибок приложения

```python
# error_codes.py
from enum import Enum

class ErrorCode(Enum):
    # Model errors
    MODEL_NOT_AVAILABLE = "MODEL_001"
    MODEL_TIMEOUT = "MODEL_002"
    MODEL_MEMORY_ERROR = "MODEL_003"
    
    # Generation errors
    GENERATION_FAILED = "GEN_001"
    INVALID_PROMPT = "GEN_002"
    CODE_EXTRACTION_FAILED = "GEN_003"
    
    # Review errors
    REVIEW_FAILED = "REV_001"
    INVALID_CODE = "REV_002"
    ANALYSIS_FAILED = "REV_003"
    
    # Communication errors
    AGENT_UNAVAILABLE = "COMM_001"
    NETWORK_ERROR = "COMM_002"
    TIMEOUT_ERROR = "COMM_003"
    
    # Validation errors
    VALIDATION_FAILED = "VAL_001"
    INVALID_INPUT = "VAL_002"
    MISSING_REQUIRED_FIELD = "VAL_003"

class ErrorHandler:
    def __init__(self):
        self.error_messages = {
            ErrorCode.MODEL_NOT_AVAILABLE: "Model service is not available",
            ErrorCode.MODEL_TIMEOUT: "Model request timed out",
            ErrorCode.MODEL_MEMORY_ERROR: "Insufficient memory for model",
            ErrorCode.GENERATION_FAILED: "Code generation failed",
            ErrorCode.INVALID_PROMPT: "Invalid prompt format",
            ErrorCode.CODE_EXTRACTION_FAILED: "Failed to extract code from response",
            ErrorCode.REVIEW_FAILED: "Code review failed",
            ErrorCode.INVALID_CODE: "Invalid code provided for review",
            ErrorCode.ANALYSIS_FAILED: "Code analysis failed",
            ErrorCode.AGENT_UNAVAILABLE: "Agent service is unavailable",
            ErrorCode.NETWORK_ERROR: "Network communication error",
            ErrorCode.TIMEOUT_ERROR: "Request timeout",
            ErrorCode.VALIDATION_FAILED: "Input validation failed",
            ErrorCode.INVALID_INPUT: "Invalid input provided",
            ErrorCode.MISSING_REQUIRED_FIELD: "Required field is missing"
        }
    
    def get_error_message(self, error_code: ErrorCode) -> str:
        """Get error message for error code."""
        return self.error_messages.get(error_code, "Unknown error")
    
    def handle_error(self, error_code: ErrorCode, details: str = "") -> dict:
        """Handle error and return error response."""
        return {
            "error_code": error_code.value,
            "error_message": self.get_error_message(error_code),
            "details": details,
            "timestamp": time.time()
        }
```

## Процедуры восстановления

### 1. Полное восстановление системы

```bash
#!/bin/bash
# full_recovery.sh

echo "Starting full system recovery..."

# Stop all services
echo "Stopping all services..."
docker-compose down

# Clean up containers and volumes
echo "Cleaning up containers and volumes..."
docker system prune -a -f
docker volume prune -f

# Remove old images
echo "Removing old images..."
docker rmi $(docker images -q) 2>/dev/null || true

# Rebuild everything
echo "Rebuilding services..."
docker-compose build --no-cache

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Verify health
echo "Verifying health..."
curl -s http://localhost:9001/health && echo "Generator OK" || echo "Generator FAIL"
curl -s http://localhost:9002/health && echo "Reviewer OK" || echo "Reviewer FAIL"

echo "Recovery completed!"
```

### 2. Восстановление после сбоя модели

```bash
#!/bin/bash
# model_recovery.sh

echo "Starting model recovery..."

# Stop model service
echo "Stopping model service..."
docker-compose stop starcoder-chat

# Clean up model container
echo "Cleaning up model container..."
docker-compose rm -f starcoder-chat

# Check GPU memory
echo "Checking GPU memory..."
nvidia-smi

# Restart model service
echo "Restarting model service..."
docker-compose up -d starcoder-chat

# Wait for model to load
echo "Waiting for model to load..."
sleep 60

# Test model
echo "Testing model..."
curl -X POST http://localhost:8003/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' \
  -w "\nHTTP Status: %{http_code}\n"

echo "Model recovery completed!"
```

### 3. Восстановление данных

```bash
#!/bin/bash
# data_recovery.sh

BACKUP_DIR="/backups"
RESTORE_DATE="$1"

if [ -z "$RESTORE_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls -la $BACKUP_DIR
    exit 1
fi

BACKUP_FILE="$BACKUP_DIR/backup_${RESTORE_DATE}.tar.gz"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting data recovery from $BACKUP_FILE..."

# Stop services
echo "Stopping services..."
docker-compose down

# Extract backup
echo "Extracting backup..."
tar -xzf "$BACKUP_FILE"

# Restore configuration
echo "Restoring configuration..."
cp -r backup_${RESTORE_DATE}/.env* .
cp -r backup_${RESTORE_DATE}/docker-compose*.yml .

# Restore data
echo "Restoring data..."
cp -r backup_${RESTORE_DATE}/results .
cp -r backup_${RESTORE_DATE}/logs .

# Start services
echo "Starting services..."
docker-compose up -d

# Cleanup
echo "Cleaning up..."
rm -rf backup_${RESTORE_DATE}

echo "Data recovery completed!"
```

## Заключение

Это руководство предоставляет комплексные решения для устранения неполадок в мульти-агентной системе StarCoder. Следуйте этим инструкциям для диагностики и решения проблем.

Ключевые принципы:
- **Систематический подход**: Следуйте шагам диагностики по порядку
- **Логирование**: Всегда проверяйте логи для понимания проблем
- **Мониторинг**: Используйте инструменты мониторинга для предотвращения проблем
- **Документирование**: Записывайте решения для будущих случаев
- **Профилактика**: Регулярно проверяйте систему на потенциальные проблемы

Для получения дополнительной информации обратитесь к:
- [Архитектурной документации](ARCHITECTURE.md)
- [Руководству разработчика](DEVELOPER_GUIDE.md)
- [Руководству по развертыванию](DEPLOYMENT.md)
