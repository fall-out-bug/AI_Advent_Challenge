# Runbook: Test Agent Service

## Service Overview

- **Service Name**: Test Agent (Epic 26)
- **Purpose**: Autonomous test agent that analyzes code, generates tests, implements code, and executes tests
- **Architecture**: Clean Architecture with Domain-Driven Design
- **Current Stage**: S1 - Domain Layer (Complete)
- **Deployment Status**: Code merged, runtime service pending (Stage 5)

## Epic 26 Status - COMPLETE ✅

**All 5 Stages Complete and Approved:**
- **S1 - Domain Layer**: 100% coverage ✅
- **S2 - Infrastructure Layer**: 90% coverage ✅
- **S3 - Application Layer - Use Cases**: 88% coverage ✅
- **S4 - Application Layer - Orchestrator**: 100% coverage ✅
- **S5 - Presentation Layer - CLI**: 96% coverage ✅

**Overall Test Coverage**: 90% (exceeds 80% requirement)
**All Acceptance Criteria**: Met ✅
**Production Ready**: Yes ✅

## Runtime Deployment - READY

**Test Agent CLI service is ready for production deployment.**

### Service Components

- **CLI Entry Point**: `src/presentation/cli/test_agent/main.py`
- **Orchestrator**: `src/application/test_agent/orchestrators/test_agent_orchestrator.py`
- **Use Cases**: GenerateTests, GenerateCode, ExecuteTests
- **Infrastructure**: TestExecutor (pytest), LLMService (Qwen), TestResultReporter

### CLI Options

**Code Viewing:**
- `--save-code`: Save generated code to `workspace/` directory
- `--show-code`: Print generated code to console

**Test Viewing:**
- `--save-tests`: Save generated tests to `workspace/` directory
- `--show-tests`: Print generated tests to console

All options can be used independently or together.

**Example Usage:**
```bash
# Save generated code to workspace/
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/01_simple_functions.py --save-code

# Show generated code in console
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/01_simple_functions.py --show-code

# Save and show both code and tests
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/01_simple_functions.py \
  --save-code --show-code --save-tests --show-tests
```

**Generated Files:**
- Code: `workspace/generated_code_{unique_id}.py`
- Tests: `workspace/generated_tests_{unique_id}.py`

### Health Checks

Following existing project patterns from `src/presentation/api/health_routes.py`:

- **Liveness**: `GET /health` - Simple health check (always returns 200 OK)
- **Readiness**: `GET /health/ready` - Detailed readiness check with dependency verification

### Monitoring

**Metrics** (to be implemented in Stage 5):
- `test_agent_requests_total` - Total requests to Test Agent
- `test_agent_test_generation_duration_seconds` - Time to generate tests
- `test_agent_code_generation_duration_seconds` - Time to generate code
- `test_agent_test_execution_duration_seconds` - Time to execute tests
- `test_agent_coverage_percentage` - Test coverage achieved
- `test_agent_errors_total` - Total errors

**Dashboards**:
- Test Agent Service Health
- Test Generation Performance
- Code Generation Performance
- Test Execution Performance

**Alerts**:
- `TestAgentServiceDown` - Service unavailable (critical)
- `TestAgentHighErrorRate` - Error rate > 1% (warning)
- `TestAgentHighLatency` - P99 latency > 5s (warning)

### Common Issues

#### Issue: Test generation fails
**Symptoms**: LLM returns invalid pytest code
**Check**:
```bash
# Check LLM service logs
kubectl logs -l app=test-agent | grep llm

# Verify Qwen model availability
curl http://localhost:8000/health/models
```
**Fix**:
- Verify Qwen model is running and accessible
- Check LLM prompt engineering in `TestAgentLLMService`
- Review pytest syntax validation in `GenerateTestsUseCase`

#### Issue: Code generation violates Clean Architecture
**Symptoms**: Generated code has layer boundary violations
**Check**:
```bash
# Run static analysis
poetry run mypy src/ --strict

# Check for layer violations
poetry run python -m src.presentation.cli.backoffice.main validate-architecture
```
**Fix**:
- Review Clean Architecture validation in `GenerateCodeUseCase`
- Ensure LLM prompts include architecture constraints
- Re-generate code with corrected prompts

#### Issue: Missing typing imports (Dict, Any, etc.)
**Symptoms**: NameError for typing types like Dict, Any in generated code
**Check**:
```bash
# Check if imports are preserved in generated test file
docker exec test-agent python -m src.presentation.cli.test_agent.main \
  /app/test_samples/04_data_processor.py --show-tests | grep -E "from typing|import.*Dict|import.*Any"
```
**Fix**:
- System now automatically detects and adds missing typing imports
- Imports are preserved during file rebuild
- If issue persists, check LLM timeout (increased to 900s for complex code)

#### Issue: Test execution fails
**Symptoms**: pytest execution returns errors
**Check**:
```bash
# Check TestExecutor logs
kubectl logs -l app=test-agent | grep pytest

# Verify test file exists and is valid
poetry run pytest tests/unit/domain/test_agent/ -v
```
**Fix**:
- Verify test file syntax is valid pytest
- Check TestExecutor error handling
- Review test execution environment

### Rollback Procedure

**Stage 1 (Current)**:
```bash
# Git-based rollback (no runtime service)
git revert <commit-hash>
git push origin main

# Verify tests pass
poetry run pytest tests/unit/domain/test_agent/ -v
```

**Stage 5 (Future - Runtime Service)**:
```bash
# Get current revision
kubectl rollout history deployment/test-agent

# Rollback to previous version
kubectl rollout undo deployment/test-agent

# Verify rollback
kubectl rollout status deployment/test-agent

# Check health
curl http://test-agent/health/ready
```

### Resource Requirements

**Production Deployment**:
- **CPU**: 500m (0.5 cores)
- **Memory**: 512Mi
- **Replicas**: 2 (min), 5 (max)
- **Scaling**: Based on CPU usage (target 70%)

### Dependencies

- **Qwen LLM Model**: Required for test and code generation
- **pytest**: Required for test execution
- **Python 3.11+**: Runtime requirement

### Contacts

- **Primary**: DevOps Team
- **Escalation**: Tech Lead
- **After Hours**: On-call engineer

### Related Documentation

- Epic 26 Specification: `docs/specs/epic_26/epic_26.md`
- Architecture: `docs/specs/epic_26/consensus/artifacts/architecture.json`
- Implementation Plan: `docs/specs/epic_26/consensus/artifacts/plan.json`
- Quality Review: `docs/specs/epic_26/consensus/artifacts/review.json`
