# Agent System v2.0 - Implementation Guide

## Overview
Token-optimized antagonistic agent system with structured communication, automated consensus, and comprehensive observability.

## Key Improvements

### 1. Token Optimization
- **Structured Data Only**: JSON/YAML instead of prose (-70% tokens)
- **3-Letter Action Codes**: REQ, ARC, PLN instead of full words
- **Reference by ID**: No content duplication
- **Delta Updates**: Only send changes, not full state

### 2. Antagonistic Design
- **Domain Veto Powers**: Each agent has absolute authority in their domain
- **Productive Tensions**: Analyst vs Architect (value vs purity)
- **Forced Consensus**: Max 3 iterations, then auto-escalate
- **No Compromises**: Architecture violations = automatic veto

### 3. New Roles
- **Unified Quality Agent**: Merged Reviewer + Tester responsibilities
- **DevOps/SRE Agent**: Deployment, monitoring, infrastructure ownership
- **Clear Boundaries**: No overlap, no gaps in responsibilities

## Implementation Checklist

### Phase 1: Setup (Day 1)
```bash
# 1. Load new agent definitions
cp docs/roles/*/role_definition_v2.yaml active/

# 2. Configure model tiers
export ANALYST_MODEL=gpt-4
export ARCHITECT_MODEL=claude-3.5-sonnet
export TECH_LEAD_MODEL=claude-3.5-sonnet
export DEVELOPER_MODEL=gpt-3.5-turbo
export QUALITY_MODEL=gpt-4
export DEVOPS_MODEL=gpt-3.5-turbo

# 3. Set token budgets (per epic)
export TOKEN_BUDGET_ANALYST=2000
export TOKEN_BUDGET_ARCHITECT=2500
export TOKEN_BUDGET_TECH_LEAD=2000
export TOKEN_BUDGET_DEVELOPER=1000
export TOKEN_BUDGET_QUALITY=2000
export TOKEN_BUDGET_DEVOPS=1500
```

### Phase 2: First Epic Test (Day 2-3)
```yaml
# Test with simple epic first
epic_test:
  id: TEST-001
  requirement: "Add health check endpoint"
  expected_iterations: 1-2
  expected_tokens: <5000
  success_criteria:
    - consensus_reached: true
    - vetos: 0
    - implementation_complete: true
```

### Phase 3: Metrics Setup (Day 4)
```bash
# 1. Deploy Prometheus
docker-compose up -d prometheus grafana

# 2. Import dashboards
curl -X POST http://grafana:3000/api/dashboards/import \
  -d @docs/roles/dashboards/*.json

# 3. Configure alerts
kubectl apply -f docs/roles/alerts/*.yaml
```

## Quick Start Commands

### Run Agent Consensus
```python
from agents.v2 import run_consensus

result = run_consensus(
    epic_id="EP-001",
    requirements="User story here",
    max_iterations=3,
    auto_escalate=True
)

print(f"Consensus: {result.status}")
print(f"Tokens used: {result.token_count}")
print(f"Iterations: {result.iterations}")
```

### Monitor Performance
```python
from metrics import agent_metrics

# Real-time metrics
metrics = agent_metrics.get_current()
print(f"Token efficiency: {metrics.token_efficiency}")
print(f"Consensus time: {metrics.consensus_time_p95}")
print(f"Architecture drift: {metrics.architecture_drift}")
```

## Communication Examples

### Structured Message (Agent-to-Agent)
```json
{
  "header": {
    "id": "msg-001",
    "from": "analyst",
    "to": "architect",
    "epic_id": "EP-001",
    "iteration": 1
  },
  "body": {
    "action": "REQ",
    "data": {
      "story": "Add health check",
      "acceptance": ["returns_200", "under_100ms"],
      "roi_hours": 2.5
    }
  }
}
```

### Veto Response
```json
{
  "response": {
    "status": "VTO",
    "reason": "LYR",
    "fix": "move_to_infrastructure"
  }
}
```

### Human Escalation
```markdown
## Consensus Failure - Epic EP-001
**Iteration:** 3/3
**Conflict:** Architecture vs Practical Implementation

### Positions
- **Architect**: Requires full refactor (LYR violation)
- **Tech Lead**: Suggests technical debt ticket
- **Quality**: Blocks due to untestable design

### Options
1. Refactor now (8 hours)
2. Technical debt + workaround (2 hours)
3. Defer to next epic

**Recommendation:** Option 2 (based on ROI)
```

## Model Cost Optimization

| Agent | Model | Tokens/Epic | Cost/Epic |
|-------|-------|------------|-----------|
| Analyst | GPT-4 | 2000 | $0.06 |
| Architect | Claude-3.5 | 2500 | $0.08 |
| Tech Lead | Claude-3.5 | 2000 | $0.06 |
| Developer | GPT-3.5 | 1000 | $0.002 |
| Quality | GPT-4 | 2000 | $0.06 |
| DevOps | GPT-3.5 | 1500 | $0.003 |
| **Total** | | **10,000** | **$0.27** |

*70% reduction from v1 system through compression and structured data*

## Troubleshooting

### Common Issues

#### 1. Consensus Timeout
```yaml
symptom: Iterations exceed 3 without agreement
diagnosis: Check veto_matrix for conflicts
solution:
  - Review domain boundaries
  - Adjust voting weights
  - Add specific resolution rule
```

#### 2. Token Budget Exceeded
```yaml
symptom: Agent stops mid-iteration
diagnosis: Check token_usage metrics
solution:
  - Increase compression
  - Switch to lower tier model
  - Reduce state size
```

#### 3. Architecture Drift
```yaml
symptom: Violations increase over time
diagnosis: Check architecture_drift metric
solution:
  - Enforce stricter gates
  - Require MADR for changes
  - Refactoring sprint
```

## Migration Path

### From v1 to v2
1. **Week 1**: Run both systems in parallel
2. **Week 2**: Route 25% traffic to v2
3. **Week 3**: Route 75% traffic to v2
4. **Week 4**: Full cutover to v2

### Rollback Plan
```bash
# If issues detected
./scripts/rollback_to_v1.sh

# Preserves v2 data for analysis
# Restores v1 agent definitions
# Switches routing back to v1
```

## Success Metrics

### Target KPIs (30 days)
- **Token Usage**: -70% reduction ✓
- **Consensus Time**: <30 min P95 ✓
- **Architecture Violations**: 0 in production ✓
- **Delivery Velocity**: +25% increase ✓
- **Cost per Epic**: <$0.30 ✓

## Next Steps

1. Review agent definitions with team
2. Set up test environment
3. Run pilot epic (TEST-001)
4. Configure monitoring
5. Train team on new protocol
6. Begin phased rollout

## Support

- **Documentation**: `docs/roles/*_v2.yaml`
- **Metrics**: http://grafana:3000/dashboard/agents
- **Logs**: `kubectl logs -f agent-system`
- **Escalation**: Create issue with label `agent-v2`

---

**Version**: 2.0
**Status**: Ready for Implementation
**Last Updated**: 2025-11-19
