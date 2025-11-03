# Phase 0: Refactoring Priorities Matrix

**Generated:** 2025-01-27  
**Scope:** Butler Agent refactoring roadmap based on Phase 0 analysis

## Executive Summary

This report consolidates insights from code quality, architecture, and test coverage analysis to provide a prioritized, actionable refactoring roadmap. Focus on high-impact, low-risk changes first, progressing to major architectural improvements.

## Priority Matrix

**Assessment Factors:**
- **Complexity:** Lines of code, cyclomatic complexity
- **Architectural Impact:** SOLID violations, layer purity
- **Test Coverage:** Current coverage, testing difficulty
- **Change Frequency:** Estimated from structure (complex = stable/foundational)
- **Risk:** Impact of breaking changes

## Top 10 Files Requiring Immediate Attention

### 1. 🔴 mcp_aware_agent.py (696 lines)

**Priority:** **CRITICAL**  
**Effort:** 16-24 hours  
**Risk:** HIGH  
**Dependencies:** Phase 1 foundation

**Issues:**
- God Class with 9 responsibilities (SRP violation)
- Domain importing infrastructure/presentation (architecture violation)
- Complexity F in `_stage_execution` (354 lines)
- Low test coverage (~20%)
- 150+ mypy errors cascading from this file

**Refactoring Strategy:**
```
Split into:
1. DecisionEngine (domain) - 4h
2. ToolExecutor (infrastructure) - 4h
3. ParameterNormalizer (domain) - 2h
4. ResponseFormatter (domain) - 2h
5. MCPAwareAgent orchestrator (domain) - 4h
6. Tests + integration - 6h
```

**Depends On:** Create domain interfaces first

**Blocks:** Application layer, presentation layer, tests

---

### 2. 🔴 butler_bot.py (554 lines)

**Priority:** **CRITICAL**  
**Effort:** 12-16 hours  
**Risk:** HIGH  
**Dependencies:** Domain layer cleanup

**Issues:**
- Multiple handler responsibilities mixed
- Natural language handling too complex
- Complexity C in 3 methods
- Moderate test coverage (~30%)
- Presentation layer coupling to domain

**Refactoring Strategy:**
```
Split into:
1. Extract ButlerOrchestrator (application) - 4h
2. Create handlers for each mode - 4h
3. Simplify message handling - 2h
4. Add tests - 4h
5. Clean up - 2h
```

**Depends On:** Phase 1 domain cleanup

**Blocks:** Presentation layer, E2E tests

---

### 3. 🟠 pdf_digest_tools.py (406 lines)

**Priority:** **HIGH**  
**Effort:** 8-12 hours  
**Risk:** MEDIUM  
**Dependencies:** Independent

**Issues:**
- Large file with multiple tool functions
- No complexity violations (functions OK)
- Test coverage ~40%
- Integration with MongoDB needs isolation

**Refactoring Strategy:**
```
Organize into:
1. Group related tools by module - 2h
2. Extract shared logic - 2h
3. Add comprehensive tests - 4h
4. Fix async issues - 2h
```

**Depends On:** None (can be parallel)

**Blocks:** None critical

---

### 4. 🟠 Architecture Layer Violations

**Priority:** **HIGH**  
**Effort:** 6-8 hours  
**Risk:** LOW (foundational)  
**Dependencies:** None

**Issues:**
- Domain importing outer layers
- No interfaces/protocols defined
- Circular dependencies

**Refactoring Strategy:**
```
Create interfaces:
1. domain/interfaces/tool_client.py - 1h
2. domain/interfaces/llm_client.py - 1h
3. domain/interfaces/config.py - 1h
4. Update imports in domain - 2h
5. Add tests for protocols - 2h
```

**Depends On:** None

**Blocks:** mcp_aware_agent.py refactoring

---

### 5. 🟡 intent_orchestrator.py (155 lines)

**Priority:** **MEDIUM**  
**Effort:** 4-6 hours  
**Risk:** MEDIUM  
**Dependencies:** Test fixes

**Issues:**
- Good delegation pattern ✓
- 2 test failures (IntentOrchestrator.__init__ signature changed)
- Coverage ~50%
- Can serve as template for Phase 1

**Refactoring Strategy:**
```
Improvements:
1. Fix test failures - 1h
2. Add missing tests - 2h
3. Add type hints - 1h
4. Document patterns - 1h
```

**Depends On:** None

**Blocks:** None

---

### 6. 🟡 mcp_client_robust.py (254 lines)

**Priority:** **MEDIUM**  
**Effort:** 4-6 hours  
**Risk:** LOW  
**Dependencies:** None

**Issues:**
- Well-structured retry logic ✓
- Coverage ~60%
- Good error handling ✓
- Needs protocol implementation

**Refactoring Strategy:**
```
Enhancements:
1. Implement domain interface - 2h
2. Add more tests - 2h
3. Improve metrics - 1h
```

**Depends On:** Domain interfaces creation

**Blocks:** None

---

### 7. 🟡 Test Infrastructure Fixes

**Priority:** **MEDIUM**  
**Effort:** 8-12 hours  
**Risk:** LOW  
**Dependencies:** None

**Issues:**
- 68 test errors (event loops, imports)
- 20 test failures
- MongoDB connection issues
- Event loop cleanup problems

**Refactoring Strategy:**
```
Fix issues:
1. Fix event loop issues - 4h
2. Fix import errors - 2h
3. Add test fixtures - 2h
4. Fix MongoDB mocking - 2h
```

**Depends On:** None

**Blocks:** Development speed, quality gates

---

### 8. 🟢 pyproject.toml Type Stubs

**Priority:** **LOW**  
**Effort:** 2 hours  
**Risk:** NONE  
**Dependencies:** None

**Issues:**
- Missing type stubs: yaml, dateparser, pytz
- 10+ mypy import errors

**Refactoring Strategy:**
```
Quick fixes:
1. Install types-yaml - 10min
2. Install types-dateparser - 10min
3. Install types-pytz - 10min
4. Run mypy, fix remaining - 1h
```

**Depends On:** None

**Blocks:** Type checking accuracy

---

### 9. 🟢 flake8 Style Fixes

**Priority:** **LOW**  
**Effort:** 4-6 hours  
**Risk:** NONE  
**Dependencies:** None

**Issues:**
- 2,649 style violations
- Mostly whitespace, line length

**Refactoring Strategy:**
```
Automated fixes:
1. Run black --line-length=79 - 30min
2. Run autoflake - 30min
3. Fix remaining manually - 3h
```

**Depends On:** None

**Blocks:** Code readability

---

### 10. 🟢 Create Phase 1 New Files

**Priority:** **MEDIUM** (timing-dependent)  
**Effort:** 20-30 hours  
**Risk:** MEDIUM  
**Dependencies:** Domain interfaces, mcp_aware_agent split

**Issues:**
- Need new files per Phase 1 plan
- Must follow TDD (tests first)

**Refactoring Strategy:**
```
New files (from plan):
1. domain/agents/services/decision_engine.py - 4h
2. domain/agents/services/tool_executor.py - 4h
3. domain/agents/services/response_formatter.py - 3h
4. application/orchestrators/butler_orchestrator.py - 6h
5. application/usecases/create_task_usecase.py - 4h
6. application/usecases/collect_data_usecase.py - 4h
7. Tests for all above - 8h
```

**Depends On:** Domain split, test infrastructure

**Blocks:** Phase 2-7 progress

---

## Quick Wins (<2 hours each)

### Immediate Actions (Do First)

1. **Install type stubs** (30 min)
   - `poetry add --group dev types-PyYAML types-dateparser types-pytz`
   - Effort: 30min, Risk: None

2. **Fix mypy comment syntax** (15 min)
   - Already done: `agent_metrics.py` line 79
   - Effort: Done ✓

3. **Fix obvious test failures** (1h)
   - FromEnv → FromORM issues
   - Effort: 1h, Risk: Low

4. **Run black formatter** (30 min)
   - `poetry run black src --line-length=79`
   - Effort: 30min, Risk: None

5. **Create domain interfaces** (2h)
   - Protocols for tool, LLM, config
   - Effort: 2h, Risk: Low, Blocks: Everything

---

## Dependency Order

### Stage 1: Foundation (Week 1)

```
1. Create domain interfaces (2h) ──┐
2. Fix test infrastructure (8h) ──┤──→ Foundation ready
3. Quick wins (4h) ─────────────┘
```

**Output:** Clean base for refactoring

### Stage 2: Domain Split (Week 2)

```
1. Split mcp_aware_agent.py (16-24h)
   └─→ Create DecisionEngine
   └─→ Create ToolExecutor  
   └─→ Create ParameterNormalizer
   └─→ Create ResponseFormatter
   └─→ Update orchestration
```

**Output:** Clean domain layer

### Stage 3: Application Layer (Week 3)

```
1. Create ButlerOrchestrator (4h)
2. Create CreateTaskUseCase (4h)
3. Create CollectDataUseCase (4h)
4. Wire dependencies (4h)
```

**Output:** Working application layer

### Stage 4: Presentation Cleanup (Week 4)

```
1. Update butler_bot.py (12-16h)
2. Update handlers (8h)
3. Fix E2E tests (8h)
```

**Output:** Complete refactoring

---

## Risk Assessment

### High Risk Items

| Item | Risk | Mitigation |
|------|------|------------|
| mcp_aware_agent.py split | Breaking changes | Extensive tests first, gradual migration |
| butler_bot.py refactor | User impact | Feature flags, parallel implementation |
| Architecture changes | Integration issues | Phase-by-phase, incremental |

### Low Risk Items

| Item | Risk | Mitigation |
|------|------|------------|
| Type stub installation | None | Safe dependency addition |
| Style fixes (flake8) | None | Automated tools |
| Test infrastructure | Low | Isolated from production |

---

## Effort Estimates

### By Phase (from plan + analysis)

| Phase | Original Estimate | Revised Estimate | Reason |
|-------|------------------|------------------|--------|
| Phase 0 (Analysis) | 1 day | ✅ Done | Baseline established |
| Phase 1 (Domain) | 2-3 days | **3-4 days** | More complexity than expected |
| Phase 2 (Infrastructure) | 2 days | 2 days | As expected |
| Phase 3 (Application) | 2 days | **3 days** | More use cases needed |
| Phase 4 (Presentation) | 1-2 days | **2-3 days** | butler_bot needs more work |
| Phase 5 (Testing) | 2-3 days | **3-4 days** | 68 errors to fix first |
| Phase 6 (Docs) | 2 days | 2 days | As expected |
| Phase 7 (DevOps) | 2 days | 2 days | As expected |

**Total:** 14-18 days → **Revised: 18-22 days**

---

## Success Criteria by Phase

### Phase 1: Domain Layer

- ✅ No domain → infrastructure/presentation imports
- ✅ All domain files <150 lines
- ✅ All functions <40 lines
- ✅ 80% test coverage
- ✅ No cyclomatic complexity >C

### Phase 2: Infrastructure

- ✅ All infrastructure implements domain interfaces
- ✅ 80% test coverage
- ✅ No circular dependencies
- ✅ Proper DI throughout

### Phase 3: Application

- ✅ ButlerOrchestrator created
- ✅ All use cases created
- ✅ 85% test coverage
- ✅ All orchestrators tested

### Phase 4: Presentation

- ✅ butler_bot.py <200 lines
- ✅ All handlers extracted
- ✅ 70% test coverage
- ✅ E2E tests passing

### Phase 5: Testing

- ✅ 80% overall coverage
- ✅ All tests passing
- ✅ No event loop errors
- ✅ All fixtures working

### Phase 6: Documentation

- ✅ Architecture docs updated
- ✅ API docs complete
- ✅ Deployment guide done
- ✅ Code examples added

### Phase 7: DevOps

- ✅ Docker compose working
- ✅ CI/CD passing
- ✅ Monitoring set up
- ✅ Production ready

---

## Quick Reference: What to Do Next

### Week 1 Actions

1. ✅ **Create domain interfaces** (2h) - BLOCKER for everything
2. ✅ **Fix test infrastructure** (8h) - Enable development
3. ✅ **Install type stubs** (30min) - Reduce mypy errors
4. ⚠️  **Fix mypy obvious issues** (2h) - Improve quality
5. ⚠️  **Run black** (30min) - Clean up style

### Week 2 Actions

6. ✅ **Split mcp_aware_agent.py** (20h) - Core domain
7. ✅ **Add comprehensive tests** (10h) - Quality gate

### Week 3 Actions

8. ✅ **Create application layer** (16h) - Use cases
9. ✅ **Test application layer** (8h) - Quality

### Week 4 Actions

10. ✅ **Refactor presentation** (20h) - Final layer
11. ✅ **E2E testing** (8h) - Integration
12. ✅ **Documentation** (8h) - Knowledge
13. ✅ **DevOps** (8h) - Delivery

---

## Recommendations

### Do First (Critical Path)

1. **Domain interfaces** - Blocks everything
2. **Test infrastructure** - Blocks development speed
3. **Quick wins** - Build momentum

### Do Next (High Impact)

4. **mcp_aware_agent.py split** - Core architecture
5. **butler_bot.py refactor** - Presentation layer
6. **Application layer** - New functionality

### Do Last (Polish)

7. **Style fixes** - Automated
8. **Documentation** - Important but non-blocking
9. **DevOps** - Final step

---

## Lessons Learned

### What Went Well (Phase 0)

- ✅ Comprehensive analysis completed
- ✅ Clear priorities identified
- ✅ Realistic estimates provided
- ✅ Dependencies mapped

### What to Improve

- ⚠️  More automation (CI/CD earlier)
- ⚠️  Better test isolation
- ⚠️  Earlier abstraction introduction

---

## References

- [Refactoring Patterns](https://refactoring.com/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Test-Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

