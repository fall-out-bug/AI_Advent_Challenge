<!-- 1fe96aee-1811-4508-8d10-22efef61e000 a9f61f3e-49f1-4093-9c10-f64a65fce95f -->
# Phase 2: Agent Consolidation & Production Readiness

## Overview

Phase 2 consolidates all day_05-08 implementations into the Clean Architecture structure, eliminates temporary adapters, achieves 80% test coverage, and establishes production infrastructure including CI/CD, monitoring, and MLOps foundations.

## Architecture Goals

- **Single Source of Truth**: Migrate all day_XX code into `src/`, deprecate day_XX directories
- **Native Implementations**: Remove adapter layer, implement agents natively in Clean Architecture
- **Production Quality**: 80% test coverage, CI/CD pipeline, monitoring
- **MLOps Ready**: Experiment tracking, model registry, performance monitoring

## Phase 2A: Migration & Code Consolidation

### 2A.1: Migrate Day 07 Components

**Target**: Native multi-agent system in Clean Architecture

**Components to Migrate**:

- `day_07/agents/core/code_generator.py` → `src/domain/agents/code_generator.py`
- `day_07/agents/core/code_reviewer.py` → `src/domain/agents/code_reviewer.py`
- `day_07/orchestrator.py` → `src/application/orchestrators/multi_agent_orchestrator.py`
- `day_07/communication/*` → `src/domain/messaging/`

**Key Files**:

```
src/domain/agents/
├── base_agent.py (new abstract base)
├── code_generator.py (migrated)
└── code_reviewer.py (migrated)

src/domain/messaging/
├── message_schema.py (migrated)
└── message_types.py (enhanced)

src/application/orchestrators/
├── base_orchestrator.py (new)
└── multi_agent_orchestrator.py (migrated)
```

**Refactoring Required**:

- Extract base agent interface from day_07 agents
- Unify with existing `BaseAgent` concept from Phase 1
- Implement repository pattern for agent state persistence
- Add domain events for agent communication

### 2A.2: Migrate Day 08 Components

**Target**: Native token analysis and ML engineering features

**Components to Migrate**:

- `day_08/domain/entities/token_analysis.py` → integrate with existing token entities
- `day_08/domain/services/token_counter.py` → enhance existing TokenAnalyzer
- `day_08/ml/compression/*` → `src/domain/services/compression/`
- `day_08/domain/services/experiment_runner.py` → `src/application/use_cases/run_experiment.py`

**Key Files**:

```
src/domain/services/compression/
├── compressor.py (new interface)
├── strategies/
│   ├── summarization_compressor.py
│   ├── keyword_compressor.py
│   └── truncation_compressor.py

src/application/use_cases/
├── analyze_tokens.py (enhanced)
├── compress_text.py (new)
└── run_experiment.py (migrated)
```

**Integration Tasks**:

- Merge day_08 token entities with Phase 1 token value objects
- Unify compression strategies under Strategy pattern
- Integrate ML engineering patterns into application layer

### 2A.3: Migrate Day 06 Components

**Target**: Native riddle testing framework

**Components to Migrate**:

- `day_06/src/core/riddle_tester.py` → `src/domain/services/riddle_evaluator.py`
- `day_06/src/core/model_tester.py` → `src/application/use_cases/test_model.py`
- `day_06/src/data/riddles.py` → `src/infrastructure/data/riddles_repository.py`

**Key Files**:

```
src/domain/services/
└── riddle_evaluator.py (migrated)

src/application/use_cases/
├── test_model_with_riddles.py (new)
└── compare_reasoning_modes.py (new)

src/infrastructure/data/
└── riddles_repository.py (migrated)
```

### 2A.4: Migrate Day 05 Components

**Target**: Native multi-model support

**Components to Migrate**:

- `day_05/clients/model_client.py` → enhance `src/infrastructure/clients/shared_sdk_client.py`
- `day_05/business/chat_handler.py` → `src/application/use_cases/chat_interaction.py`
- `day_05/state/conversation.py` → `src/domain/entities/conversation.py`

**Key Files**:

```
src/domain/entities/
└── conversation.py (new)

src/application/use_cases/
└── chat_interaction.py (new)

src/infrastructure/clients/
└── multi_model_client.py (enhanced)
```

### 2A.5: Remove Adapters

**Action**: Delete temporary adapter layer after migration

**Files to Remove**:

- `src/infrastructure/adapters/day_07_adapter.py`
- `src/infrastructure/adapters/day_08_adapter.py`
- Update imports across codebase
- Remove adapter tests, add native tests

### 2A.6: Archive Day_XX Directories

**Action**: Move to archive, update documentation

```bash
mkdir -p archive/legacy
mv day_05 day_06 day_07 day_08 archive/legacy/
echo "# Legacy Code Archive" > archive/legacy/README.md
```

Update root README to reflect new structure.

## Phase 2B: Test Coverage to 80%+

### 2B.1: Domain Layer Tests

**Current**: 85% → **Target**: 90%+

- Add edge case tests for all entities
- Test domain service error handling
- Add property-based tests (hypothesis) for value objects

### 2B.2: Application Layer Tests

**Current**: 70% → **Target**: 85%+

- Test all use cases with mocked dependencies
- Add integration tests for orchestrators
- Test error propagation and rollback scenarios

### 2B.3: Infrastructure Layer Tests

**Current**: 60% → **Target**: 80%+

- Test repository implementations (JSON, future DB)
- Test model client error handling and retries
- Add mock server tests for external API calls

### 2B.4: Presentation Layer Tests

**Current**: 30% → **Target**: 75%+

- Add API endpoint tests (FastAPI TestClient)
- Test CLI command execution
- Add request/response validation tests

### 2B.5: E2E Tests

**New**: Comprehensive end-to-end workflows

- Code generation → review workflow
- Multi-model comparison workflow
- Token analysis → compression workflow
- Riddle testing workflow

## Phase 2C: Production Infrastructure

### 2C.1: CI/CD Pipeline

**Tool**: GitHub Actions (or GitLab CI)

**Pipeline Stages**:

```yaml
# .github/workflows/ci.yml
stages:
  - lint (black, flake8, mypy)
  - test (pytest with coverage)
  - security (bandit, safety)
  - build (Docker image)
  - deploy (staging/production)
```

**Key Jobs**:

- Automated testing on every PR
- Coverage reporting (codecov.io)
- Automated Docker builds
- Deployment to staging on merge to main

### 2C.2: Monitoring & Observability

**Stack**: Prometheus + Grafana + Loki

**Metrics to Track**:

- Request latency (p50, p95, p99)
- Token usage per model
- Error rates by endpoint
- Model response quality metrics

**Implementation**:

```
src/infrastructure/monitoring/
├── metrics.py (Prometheus metrics)
├── logging.py (structured logging)
└── tracing.py (OpenTelemetry integration)
```

### 2C.3: MLOps Foundations

**Experiment Tracking**: MLflow integration

```python
# src/infrastructure/ml/experiment_tracker.py
class MLflowTracker:
    """Track experiments with MLflow"""
    def log_experiment(self, params, metrics, artifacts)
    def load_model(self, run_id)
```

**Model Registry**:

- Version all model configurations
- Track model performance over time
- A/B testing infrastructure

**Key Files**:

```
src/infrastructure/ml/
├── experiment_tracker.py
├── model_registry.py
└── performance_monitor.py
```

### 2C.4: Performance Optimization

**Targets**:

- API response time < 10s (95th percentile)
- Support 10+ concurrent requests
- Efficient memory usage (GPU/CPU)

**Optimizations**:

- Connection pooling for model clients
- Response caching (Redis)
- Async processing for long-running tasks
- Load testing with Locust/k6

## Phase 2D: Missing Features

### 2D.1: Configuration-Driven Model Selection

**File**: `src/infrastructure/config/model_selector.py`

```python
class ModelSelector:
    """Select models based on YAML configuration"""
    def select_by_task(self, task_type: str) -> ModelConfig
    def select_by_constraints(self, max_tokens, latency) -> ModelConfig
```

### 2D.2: Parallel Agent Execution

**File**: `src/application/orchestrators/parallel_orchestrator.py`

```python
class ParallelOrchestrator:
    """Execute multiple agents in parallel"""
    async def execute_parallel(self, agents: List[BaseAgent])
```

### 2D.3: Automatic Compression on Limit Exceed

**Enhancement**: Extend TokenAnalyzer with auto-compression

```python
class SmartTokenAnalyzer(TokenAnalyzer):
    """Automatically compress when approaching limits"""
    def analyze_and_compress(self, text: str, limit: int)
```

### 2D.4: Custom Experiment Templates

**File**: `src/domain/templates/experiment_template.py`

```python
class ExperimentTemplate:
    """Define reusable experiment configurations"""
    def create_from_yaml(self, template_path: str)
```

### 2D.5: Automated Refactoring Suggestions

**File**: `src/domain/services/refactoring_suggester.py`

Uses AST analysis to suggest refactorings based on code quality metrics.

## Success Criteria

### Phase 2A (Migration)

- [ ] All day_07 components migrated natively into src/
- [ ] All day_08 components migrated natively into src/
- [ ] All day_06 components migrated natively into src/
- [ ] All day_05 components migrated natively into src/
- [ ] Adapter layer completely removed
- [ ] Day_XX directories archived
- [ ] All existing functionality works through new structure

### Phase 2B (Testing)

- [ ] Overall test coverage ≥ 80%
- [ ] Domain layer coverage ≥ 90%
- [ ] Application layer coverage ≥ 85%
- [ ] Infrastructure layer coverage ≥ 80%
- [ ] Presentation layer coverage ≥ 75%
- [ ] 10+ comprehensive E2E tests

### Phase 2C (Production)

- [ ] CI/CD pipeline operational
- [ ] Automated testing on all PRs
- [ ] Docker builds automated
- [ ] Prometheus metrics exposed
- [ ] Grafana dashboards created
- [ ] MLflow tracking integrated
- [ ] Performance benchmarks meet targets

### Phase 2D (Features)

- [ ] Configuration-driven model selection working
- [ ] Parallel orchestrator functional
- [ ] Auto-compression on limit exceed
- [ ] Experiment templates implemented
- [ ] Refactoring suggester operational

## Timeline Estimate

- **Phase 2A**: 8-12 days (migration is complex)
- **Phase 2B**: 5-7 days (test expansion)
- **Phase 2C**: 6-8 days (infrastructure setup)
- **Phase 2D**: 5-7 days (feature development)
- **Total**: 24-34 days (~5-7 weeks)

## Risk Mitigation

**Risk**: Breaking changes during migration

- **Mitigation**: Maintain adapters until full migration complete, comprehensive testing

**Risk**: Test coverage expansion takes longer than expected

- **Mitigation**: Prioritize critical path coverage first, parallelize test writing

**Risk**: Infrastructure setup complexity

- **Mitigation**: Use managed services where possible (GitHub Actions, cloud monitoring)

## Documentation Updates

- [ ] Update root README with new structure
- [ ] Create migration guide for future components
- [ ] Document CI/CD pipeline
- [ ] Create monitoring playbook
- [ ] Update API documentation
- [ ] Write MLOps guide

### To-dos

- [ ] Migrate day_07 components (agents, orchestrator, communication) into src/ with native Clean Architecture implementation
- [ ] Migrate day_08 components (token analysis, compression, ML features) into src/ domain and application layers
- [ ] Migrate day_06 riddle testing framework into src/ as native domain service and use case
- [ ] Migrate day_05 multi-model client and chat functionality into src/ infrastructure and application layers
- [ ] Remove temporary adapter layer after migration validation, update all imports
- [ ] Archive day_05-08 directories to archive/legacy/ and update documentation
- [ ] Expand domain layer test coverage from 85% to 90%+ with edge cases and property-based tests
- [ ] Expand application layer test coverage from 70% to 85%+ with all use cases and orchestrators
- [ ] Expand infrastructure layer test coverage from 60% to 80%+ with repository and client tests
- [ ] Expand presentation layer test coverage from 30% to 75%+ with API and CLI tests
- [ ] Create 10+ comprehensive E2E tests for full workflows (generation→review, multi-model, compression)
- [ ] Set up CI/CD pipeline with GitHub Actions (lint, test, security, build, deploy stages)
- [ ] Implement monitoring with Prometheus metrics, structured logging, and Grafana dashboards
- [ ] Integrate MLflow for experiment tracking, model registry, and performance monitoring
- [ ] Optimize performance (connection pooling, caching, async processing) and validate with load testing
- [ ] Implement configuration-driven model selection based on task type and constraints
- [ ] Implement parallel agent execution orchestrator for concurrent agent operations
- [ ] Implement automatic compression when token limits are approached
- [ ] Create custom experiment template system with YAML configuration
- [ ] Implement automated refactoring suggestions using AST analysis