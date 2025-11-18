# Tech Lead Day Capabilities

<<<<<<< HEAD
## Foundational Days 1-22

### Days 1-10 · Planning Framework
- Create plan templates with stages, DoD, and evidence mapping.
- Define CI gate catalogue (lint, tests, coverage, security).
- Establish risk register and rollback checklist formats.

### Day 11 · Shared Infra & MCP Baseline
- Incorporate shared infra bring-up steps into staging plan.
- Align plan checkpoints with MCP tool availability and observability.
- Coordinate with operations for environment variables and secrets.

### Day 12 · Deployment & Quick Start
- Integrate quick-start commands into rollout sequence.
- Validate health checks and smoke tests in plan DoD.
- Document local vs CI parity steps for Developers.

### Day 15 · Modular Reviewer Rollout
- Stage feature-flag rollout and fallback strategy.
- Specify CI coverage for reviewer performance metrics.
- Sync with Architect on adapter interfaces and migration path.

### Day 17 · Integration Contracts & README
- Ensure integration scenarios cover API endpoints and contract validation.
- Update README references and align plan tasks with documentation updates.
- Capture cross-team dependencies and communication plans.

### Days 18-22 · Execution Support
- Monitor stage completion and adjust plan sequencing if blockers emerge.
- Keep risk register current; escalate unresolved architecture questions.
- Prepare post-implementation review package.

## Capability Patterns
- **Stage Tables**: Include columns for owner, DoD, evidence, blockers.
- **CI Gate Matrix**: Map each stage to required pipelines and commands.
- **Risk Register**: Track likelihood, impact, owner, mitigation, status.

## Upcoming (Days 23-28) ⏳
- Plan for analytics tooling integration and performance budgets.
- Expand rollback scenarios for multi-service deployments.
- Prepare staged dry-runs using feature flags and canary strategies.

## Update Log
- [ ] EP19 – Draft plan pending Analyst approval
- [ ] EP20 – Awaiting architecture inputs
- [ ] EP21 – Aligning reviewer rollout with operations window
=======
This document details how each Challenge Day enhances the Tech Lead role's capabilities in creating staged implementation plans, defining CI/CD gates, managing risks, and coordinating deployment strategies.

---

## Day 1 · Staged Planning Basics
**Capability:** Create staged implementation plans with clear ownership and DoD
**Use Case:** Break 8 requirements into 5 stages with owners, DoD, evidence
**Key Technique:** Map requirements → stages → tasks → CI gates
**Example:**
```markdown
## Stage 1: Foundation Setup (3 days, Owner: DevOps)
- Tasks: Setup MongoDB, Configure Prometheus, Create CI pipeline
- DoD: MongoDB accessible, /metrics endpoint works, CI pipeline green
- Evidence: Connection test passed, Grafana dashboard shows metrics
```
**Status:** ✅ MASTERED (Day 1)

---

## Day 2 · Structured Plan Output
**Capability:** Output plans in parseable JSON format for tracking
**Use Case:** Plan with stages → JSON → Track in project management tool
**Key Technique:** Use standardized schema with stages, tasks, DoD, blockers
**Status:** ✅ MASTERED (Day 2)

---

## Day 3 · Plan Completeness Validation
**Capability:** Know when plan is complete enough for Developer handoff
**Use Case:** Check: All requirements covered? CI gates defined? Risks documented?
**Key Technique:** Completeness score: requirements_coverage + ci_gates + risk_coverage
**Status:** ✅ MASTERED (Day 3)

---

## Day 4 · Temperature Tuning for Planning
**Capability:** Use T=0.7 for risk brainstorming, T=0.0 for CI gate generation
**Status:** ✅ MASTERED (Day 4)

---

## Day 5 · Model Selection for Planning
**Capability:** Use Claude Sonnet 4.5 for complex plans, GPT-4o-mini for simple tasks
**Status:** ✅ MASTERED (Day 5)

---

## Day 6 · Chain of Thought Plan Validation
**Capability:** Use CoT to validate plan for missing steps, dependencies, bottlenecks
**Use Case:** "Think step-by-step: Can Developer execute this plan?" → Finds gaps
**Key Technique:** CoT checklist: All dependencies clear? Rollback defined? Tests specified?
**Example:** Without CoT: 0 gaps found. With CoT: 3 critical gaps (missing DB migration, no rollback, tests undefined)
**Status:** ✅ MASTERED (Day 6)

---

## Day 7 · Multi-Agent Plan Review
**Capability:** Second Tech Lead reviews plan before Developer handoff
**Use Case:** Tech Lead A creates plan → Tech Lead B reviews → Only approved plans go to Developer
**Status:** ✅ MASTERED (Day 7)

---

## Day 8 · Token Management for Plans
**Capability:** Manage 12K token budget for complex plans
**Breakdown:** Architecture (2K) + Stages (4K) + CI gates (2K) + Risks (1K) + Handoff (2K) = 11K
**Status:** ✅ MASTERED (Day 8)

---

## Day 9 · MCP Integration for Planning
**Capability:** Query MCP for past implementation plans
**Use Case:** "Find similar payment system plans" → Discover EP15, EP19 plans → Reuse stage structure
**Status:** ✅ MASTERED (Day 9)

---

## Day 10 · Custom Validation Tools
**Capability:** Create MCP tool to validate plans against standards
**Use Case:** validate_plan(epic_id) → Check: All stages have DoD? CI gates defined? Risks documented?
**Status:** ✅ MASTERED (Day 10)

---

## Day 11 · Shared Infrastructure Planning
**Capability:** Embed shared infra setup steps in plan
**Use Case:** Stage 1 always includes: MongoDB setup, Prometheus config, Grafana dashboard
**Key Technique:** Auto-inject infra stages from shared_infra.md
**Example:**
```markdown
## Stage 1: Infrastructure Setup (2 days)
- MongoDB: Connect to shared cluster (mongodb://shared-mongo:27017)
- Prometheus: Configure /metrics endpoint
- Grafana: Deploy dashboard from template
- Loki: Setup structured logging
```
**Status:** ✅ MASTERED (Day 11)

---

## Day 12 · Deployment Strategy Planning
**Capability:** Define deployment topology and rollout strategy
**Use Case:** Plan canary deployment: 10% → 50% → 100% with rollback at each stage
**Key Technique:** Deployment stages: Local → Staging → Canary (10%) → Canary (50%) → Production (100%)
**Example:**
```markdown
## Stage 8: Production Deployment (Canary)
- Step 1: Deploy to 10% of prod pods (1/10 replicas)
- Monitor: Error rate < 1%, latency p95 < 2s for 1 hour
- If OK: Proceed to 50%
- If NOT OK: Rollback to previous version (< 5 minutes)
- Rollback Command: kubectl rollout undo deployment/payment-service
```
**Status:** ✅ MASTERED (Day 12)

---

## Day 13 · Testing Strategy Planning
**Capability:** Define test stages: unit → integration → E2E
**Use Case:** Stage 3: Unit tests (100% domain), Stage 5: Integration tests (80% app+infra), Stage 7: E2E (critical paths)
**Status:** ✅ MASTERED (Day 13)

---

## Day 14 · CI/CD Gate Definition
**Capability:** Define CI gates for each stage
**Use Case:** Stage gates: lint (flake8), typecheck (mypy), tests (pytest), coverage (80%), security (bandit)
**Key Technique:** Map stages → CI gates → Commands
**Example:**
```yaml
## CI Gate Matrix
| Stage | Gate | Command | Threshold | Blocking |
|-------|------|---------|-----------|----------|
| 2 | Lint | make lint | 0 errors | Yes |
| 2 | Typecheck | mypy src/ --strict | 100% coverage | Yes |
| 3 | Unit Tests | pytest tests/unit/ | All pass | Yes |
| 3 | Coverage | pytest --cov=src | ≥80% | Yes |
| 5 | Integration | pytest tests/integration/ | All pass | Yes |
| 6 | Security | bandit -r src/ | No high/medium | Yes |
| 7 | E2E | pytest tests/e2e/ | Critical paths pass | Yes |
```
**Status:** ✅ MASTERED (Day 14)

---

## Day 15 · Plan Compression
**Capability:** Compress verbose plans 50% while preserving stages, DoD, CI gates
**Use Case:** 6K token plan → 3K compressed (remove verbose descriptions, keep structure)
**Status:** ✅ MASTERED (Day 15)

---

## Day 16 · Plan Version Control
**Capability:** Track plan changes across iterations
**Use Case:** Plan v1.0 → v1.1 (added security stage) → v1.2 (adjusted timeline)
**Status:** ✅ MASTERED (Day 16)

---

## Day 17 · Integration Test Planning
**Capability:** Define integration scenarios and contract tests
**Use Case:** Stage 6: Integration Tests - validate API contracts, event schemas, database operations
**Key Technique:** Use OpenAPI contracts for API tests, JSON schemas for events
**Status:** ✅ MASTERED (Day 17)

---

## Day 18 · Real-World Deployment Planning
**Capability:** Plan for production concerns: secrets, monitoring, rollback
**Use Case:** Stage 8: Production deployment with secrets management, health checks, rollback procedure
**Status:** ✅ MASTERED (Day 18)

---

## Day 19 · Test Plan Documentation
**Capability:** Document test strategy for RAG retrieval
**Use Case:** Future projects query: "Find payment system test plans" → Discover EP23 test strategy
**Status:** ✅ MASTERED (Day 19)

---

## Day 20 · RAG Queries for Plan Reuse
**Capability:** Query past plans to reuse proven strategies
**Use Case:** "Find canary deployment plans" → Discover EP21 successful canary pattern → Reuse
**Key Technique:** Query by: deployment_strategy, complexity, success_rate
**Status:** ✅ MASTERED (Day 20)

---

## Day 21 · Plan Ranking & Filtering
**Capability:** Rank past plans by success rate and relevance
**Use Case:** 10 plans found → Filter: success_rate > 90% → Rank by similarity → Top 3
**Status:** ✅ MASTERED (Day 21)

---

## Day 22 · Plan Citations & Traceability
**Capability:** Cite past plans in current planning
**Use Case:** "Canary strategy follows EP21 successful pattern (95% success rate, 0 rollbacks)"
**Impact:** 30% planning time reduction, proven strategies reused
**Status:** ✅ MASTERED (Day 22)

---

## Capability Summary Matrix
| Day | Capability | Key Benefit |
|-----|------------|-------------|
| 1 | Staged Planning | Clear ownership + DoD |
| 3 | Completeness Validation | Know when ready for handoff |
| 6 | CoT Validation | Catch missing steps |
| 11 | Shared Infra Planning | Consistent setup |
| 12 | Deployment Strategy | Safe production rollout |
| 14 | CI/CD Gates | Automated quality |
| 20 | RAG Plan Reuse | 30% time savings |
| 22 | Citations | Traceability + proven patterns |
>>>>>>> origin/master
