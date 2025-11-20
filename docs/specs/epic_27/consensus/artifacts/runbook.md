# Runbook: Epic 27 - Enhanced Test Agent

## Service Overview

- **Service Name**: Test Agent CLI (Enhanced with Chunking)
- **Epic**: Epic 27
- **Purpose**: Generate high-quality unit and integration tests for Python modules, with support for large modules via code chunking
- **Dependencies**:
  - GigaChat LLM service (`llm-api-gigachat:8000`)
  - pytest (for test execution)
  - Python 3.11
- **SLA**: 99.9% availability
- **Deployment Method**: Docker Compose

## Architecture Changes from Epic 26

### Key Enhancements
1. **Code Chunking**: Splits large modules into semantically meaningful chunks
2. **Code Summarization**: Preserves context across chunks using LLM
3. **Coverage Aggregation**: Ensures ≥80% coverage across all chunks
4. **GigaChat Migration**: Switched from Qwen (llm-api) to GigaChat (llm-api-gigachat)

### Backward Compatibility
- Small modules (<4000 tokens) work exactly as Epic 26 (no chunking)
- Large modules automatically use chunking strategies
- All Epic 26 tests must pass (regression suite)

## Monitoring

### Dashboards
- **Service Health**: https://grafana/d/test-agent-health-epic27
- **Chunking Performance**: https://grafana/d/test-agent-chunking

### Key Metrics
- `test_agent_requests_total` - Total invocations
- `test_agent_chunking_duration_seconds` - Chunking performance
- `test_agent_token_count_accuracy` - Token counting accuracy (critical)
- `test_agent_coverage_percentage` - Test coverage achieved
- `test_agent_llm_errors_total` - GigaChat connectivity issues

### Alerts
- **TestAgentServiceDown** (critical) - Service unavailable
- **TestAgentLLMServiceDown** (critical) - GigaChat service issues
- **TestAgentTokenCountInaccurate** (warning) - Token accuracy <90%
- **TestAgentLowCoverage** (info) - Coverage <80%

### Logs
- **Container logs**: `docker logs test-agent`
- **Application logs**: `app=test-agent component=chunker|summarizer|token_counter`
- **LLM logs**: `app=test-agent component=llm_service`

## Common Issues

### Issue: GigaChat LLM Service Unavailable

**Symptoms**:
- `test_agent_llm_errors_total` increasing
- Test generation failing with connection errors
- Health check failures

**Check**:
```bash
# Verify llm-api-gigachat service is running
docker ps | grep llm-api-gigachat

# Check network connectivity
docker network inspect infra_infra_app-network | grep llm-api-gigachat

# Test connectivity from test-agent container
docker exec test-agent curl -f http://llm-api-gigachat:8000/health

# Check GigaChat service logs
docker logs llm-api-gigachat
```

**Fix**:
1. Verify `llm-api-gigachat` is running: `docker ps | grep llm-api-gigachat`
2. Verify network connection: `docker network connect infra_infra_app-network llm-api-gigachat` (if not connected)
3. Check GigaChat service health: `curl http://llm-api-gigachat:8000/health`
4. Restart test-agent if needed: `docker-compose -f docker-compose.test-agent.yml restart test-agent`

**Rollback**: If GigaChat service is down, rollback to Epic 26 (Qwen):
```bash
# Update docker-compose to use llm-api
sed -i 's|LLM_URL=.*|LLM_URL=http://llm-api:8000|' docker-compose.test-agent.yml
sed -i 's|LLM_MODEL=.*|LLM_MODEL=qwen2.5:7b|' docker-compose.test-agent.yml
docker-compose -f docker-compose.test-agent.yml up -d
```

### Issue: Token Count Accuracy Low

**Symptoms**:
- `test_agent_token_count_accuracy < 90%`
- Context overflow errors in logs
- Chunking failures

**Check**:
```bash
# Check token counter logs
docker logs test-agent | grep -i "token"

# Verify GigaChat tokenizer is being used
docker exec test-agent python -c "
from src.infrastructure.test_agent.services.token_counter import TokenCounter
tc = TokenCounter()
print(f'Tokenizer: {tc._tokenizer}')
"
```

**Fix**:
1. Verify GigaChat tokenizer library is installed correctly
2. Check tokenizer configuration matches GigaChat model
3. Verify 10% safety buffer is applied (90% of max tokens)
4. Review integration tests for token counting accuracy

**Prevention**: Monitor `test_agent_token_count_accuracy` metric. If consistently <90%, investigate tokenizer compatibility.

### Issue: Chunking Performance Degradation

**Symptoms**:
- `test_agent_chunking_duration_seconds` p99 > 5s
- Slow test generation for large modules
- High CPU usage

**Check**:
```bash
# Check chunking performance
docker exec test-agent python -c "
import time
from src.application.test_agent.services.code_chunker import CodeChunker
# Run chunking benchmark
"

# Check resource usage
docker stats test-agent

# Review chunking strategy selection
docker logs test-agent | grep -i "chunking strategy"
```

**Fix**:
1. Scale up replicas if CPU-bound: `docker-compose -f docker-compose.test-agent.yml up -d --scale test-agent=3`
2. Review chunking strategy selection logic
3. Optimize token counting (cache results if possible)
4. Consider adjusting chunk sizes if too small (more chunks = more overhead)

### Issue: Coverage Below 80%

**Symptoms**:
- `test_agent_coverage_percentage < 80`
- Alert: TestAgentLowCoverage

**Check**:
```bash
# Run coverage analysis
docker exec test-agent python -m pytest tests/ --cov=src --cov-report=term

# Check coverage aggregator logs
docker logs test-agent | grep -i "coverage"

# Review generated tests
docker exec test-agent ls -la workspace/generated_tests/
```

**Fix**:
1. Review coverage aggregator logic
2. Check for gaps in test generation (uncovered functions/classes)
3. Verify chunking strategies are generating tests for all chunks
4. Review test deduplication logic (may be removing valid tests)

### Issue: Health Check Failures

**Symptoms**:
- Container restarting frequently
- Health check endpoint returning errors
- Readiness probe failing

**Check**:
```bash
# Check health check endpoint
docker exec test-agent python -c "
import requests
response = requests.get('http://localhost:8000/health/ready')
print(f'Status: {response.status_code}')
print(f'Response: {response.text}')
"

# Check container logs
docker logs test-agent --tail 100

# Check resource constraints
docker stats test-agent
```

**Fix**:
1. Verify all dependencies are available (GigaChat, pytest, tokenizer)
2. Check resource limits (CPU/memory)
3. Review health check configuration (may be too strict)
4. Check for startup errors in logs

## Rollback Procedure

### Automatic Rollback
Rollback triggers automatically if:
- Error rate > 1% for 5 minutes
- Latency p99 > 60s for 5 minutes
- Health check failures > 10%
- GigaChat service unavailable

### Manual Rollback

**Step 1: Stop Epic 27 deployment**
```bash
docker-compose -f docker-compose.test-agent.yml down
```

**Step 2: Revert to Epic 26 configuration**
```bash
# Checkout Epic 26 deployment configuration
git checkout epic_26_deployment docker-compose.test-agent.yml

# Or manually update environment variables
sed -i 's|LLM_URL=.*|LLM_URL=http://llm-api:8000|' docker-compose.test-agent.yml
sed -i 's|LLM_MODEL=.*|LLM_MODEL=qwen2.5:7b|' docker-compose.test-agent.yml
```

**Step 3: Deploy Epic 26**
```bash
docker-compose -f docker-compose.test-agent.yml up -d
```

**Step 4: Verify rollback**
```bash
# Check service is running
docker ps | grep test-agent

# Verify health
docker exec test-agent python -c "import sys; sys.exit(0)"

# Run smoke tests
docker exec test-agent python -m pytest tests/integration/ -k 'smoke' -v
```

**Step 5: Monitor**
- Verify metrics return to normal
- Check Epic 26 tests pass
- Confirm no regressions

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] All Epic 27 stages complete and approved
- [ ] All tests passing (unit, integration, E2E)
- [ ] Epic 26 regression tests passing
- [ ] GigaChat service (`llm-api-gigachat`) running and healthy
- [ ] Network connectivity verified (`infra_infra_app-network`)
- [ ] Token counting accuracy validated
- [ ] Chunking strategies tested with real workloads
- [ ] Monitoring dashboards configured
- [ ] Alerts configured and tested
- [ ] Rollback plan tested

### Deployment Steps

**1. Deploy to Dev**
```bash
docker-compose -f docker-compose.test-agent.yml up -d --build
docker-compose -f docker-compose.test-agent.yml logs -f test-agent
```

**2. Run Smoke Tests**
```bash
docker exec test-agent python -m pytest tests/integration/ -k 'smoke' -v
```

**3. Verify GigaChat Connectivity**
```bash
docker exec test-agent python -c "
import os
import requests
llm_url = os.getenv('LLM_URL', 'http://llm-api-gigachat:8000')
response = requests.get(f'{llm_url}/health', timeout=5)
assert response.status_code == 200
"
```

**4. Deploy to Staging**
```bash
# Same as dev, but with extended monitoring
docker-compose -f docker-compose.test-agent.yml up -d --build

# Soak test for 2 hours
# Monitor metrics and logs
```

**5. Deploy to Production (Canary)**
```bash
# Deploy with 10% traffic (1 replica)
docker-compose -f docker-compose.test-agent.yml up -d --scale test-agent=1 --build

# Monitor for 2 hours
# Gradually increase: 10% → 25% → 50% → 100%
docker-compose -f docker-compose.test-agent.yml up -d --scale test-agent=2
```

## Contacts

- **Primary**: DevOps Team
- **Escalation**: Tech Lead
- **After Hours**: On-call engineer
- **LLM Service**: Infrastructure Team (for GigaChat service issues)

## Related Documentation

- Epic 26 Deployment: `docs/specs/epic_26/consensus/artifacts/deployment.json`
- Epic 27 Architecture: `docs/specs/epic_27/consensus/artifacts/architecture.json`
- Epic 27 Plan: `docs/specs/epic_27/consensus/artifacts/plan.json`
