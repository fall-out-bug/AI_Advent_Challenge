# Architect Role Examples

This directory contains detailed examples demonstrating how the Architect role applies day-by-day capabilities to design Clean Architecture systems, validate decisions with CoT, and produce actionable MADRs.

---

## Day-by-Day Examples

### Day 6 · Chain of Thought Architecture Validation

**File:** [`day_6_cot_validation.md`](day_6_cot_validation.md)

**Purpose:** Demonstrates using CoT prompting to validate architecture for circular dependencies, performance bottlenecks, and security risks before handoff.

**Key Findings:**
- **Without CoT:** 0 issues found → 5 production problems
- **With CoT:** 5 critical issues caught in design phase → 0 production problems
- **ROI:** 1 hour CoT validation → 3 weeks rework saved (120x return)

**Metrics:**
```
Circular Dependencies: 3 found and fixed
Performance: 1,250ms → 50ms latency (96% improvement)
SPOF Eliminated: Added load balancing + 5 replicas
Time Saved: 3 weeks (avoided implementation rework)
```

**Related:** See [`../day_capabilities.md#day-6`](../day_capabilities.md#day-6)

---

### Day 11 · Shared Infrastructure Integration

**File:** [`day_11_shared_infra.md`](day_11_shared_infra.md)

**Purpose:** Shows how to embed shared infrastructure constraints (MongoDB, Prometheus, Grafana) in architecture design.

**Key Elements:**
- MongoDB collections and indexes
- Prometheus metrics endpoints
- Grafana dashboard templates
- Loki structured logging format

**Benefit:** 2 hours saved (no infrastructure setup), consistency across services

**Related:** See [`../day_capabilities.md#day-11`](../day_capabilities.md#day-11)

---

### Day 12 · Deployment Topology Design

**File:** [`day_12_deployment_topology.md`](day_12_deployment_topology.md)

**Purpose:** Demonstrates multi-environment deployment architecture with health checks and rollout strategies.

**Environments:**
- Local: Docker Compose (1 replica)
- Staging: Kubernetes (3 replicas)
- Production: Kubernetes (10 replicas, canary rollout)

**Health Checks:**
- `/health`: Liveness probe
- `/ready`: Readiness probe

**Related:** See [`../day_capabilities.md#day-12`](../day_capabilities.md#day-12)

---

### Day 17 · Integration Contracts & API Design

**File:** [`day_17_integration_contracts.md`](day_17_integration_contracts.md)

**Purpose:** Shows OpenAPI 3.0 contract definition and event schema for integration testing.

**Contents:**
- REST API contract (OpenAPI spec)
- Event contract (message bus schema)
- Contract validation in CI
- Auto-generated documentation

**Related:** See [`../day_capabilities.md#day-17`](../day_capabilities.md#day-17)

---

## Example Matrix

| Day | Capability | Example File | Key Metric | Integration Impact |
|-----|------------|--------------|------------|-------------------|
| 6 | CoT Validation | `day_6_cot_validation.md` | 120x ROI | Prevents 5 production issues |
| 11 | Shared Infra | `day_11_shared_infra.md` | 2h setup saved | Consistency across services |
| 12 | Deployment | `day_12_deployment_topology.md` | 3 environments | DevOps ready |
| 17 | Contracts | `day_17_integration_contracts.md` | Auto-docs | Developer clarity |

---

## Cross-Cutting Examples

### Handoff Quality

**File:** [`../../operational/handoff_contracts.md#example-2`](../../operational/handoff_contracts.md#example-2)

Contains full Architect → Tech Lead handoff example with:
- Architecture vision
- Component list with responsibilities
- 2 MADRs (MongoDB choice, provider abstraction)
- Deployment topology
- Quality metrics

---

## How to Use These Examples

### For Architect Agents
1. **Study patterns** - especially Day 6 CoT validation checklist
2. **Reuse MADRs** - reference similar decisions from past epics
3. **Follow templates** - use example formats for consistency
4. **Validate before handoff** - apply Day 6 checklist

### For Tech Lead Agents
1. **Understand architecture** - examples show expected input quality
2. **Reference MADRs** - understand design rationale
3. **Check contracts** - Day 17 examples show expected API specs
4. **Validate readiness** - ensure examples' quality standards met

---

## Related Documentation

- **Capabilities:** [`../day_capabilities.md`](../day_capabilities.md) - Full Day 1-22 techniques
- **RAG Queries:** [`../rag_queries.md`](../rag_queries.md) - MongoDB query patterns
- **Role Definition:** [`../role_definition.md`](../role_definition.md) - Architect purpose
- **Handoff Contracts:** [`../../operational/handoff_contracts.md`](../../operational/handoff_contracts.md) - Cross-role handoffs

---

## Changelog

- **2025-11-15**: Created comprehensive examples for Days 6, 11, 12, 17
- **2025-11-15**: Enhanced rag_queries.md with example results and token costs
- **2025-11-15**: Expanded day_capabilities.md with Days 1-22 details
