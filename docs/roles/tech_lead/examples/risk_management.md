# Risk Management & Mitigation

## Risk Register Template

```json
{
  "epic": "EP23",
  "risks": [
    {
      "id": "RISK-001",
      "description": "Third-party API (Stripe) rate limits during load testing",
      "category": "external_dependency",
      "likelihood": "medium",
      "impact": "high",
      "severity_score": 8,
      "mitigation": {
        "strategy": "Circuit breaker + fallback to secondary provider",
        "implementation": "Use PayPal as fallback within 5s",
        "verification": "Load test with Stripe API mocked as down"
      },
      "owner": "Dev B",
      "status": "mitigated",
      "residual_risk": "low"
    },
    {
      "id": "RISK-002",
      "description": "Database migration fails in production",
      "category": "deployment",
      "likelihood": "low",
      "impact": "critical",
      "severity_score": 7,
      "mitigation": {
        "strategy": "Backward-compatible schema changes only",
        "implementation": "Add columns before code deploy, drop after rollback window",
        "verification": "Test rollback scenario in staging"
      },
      "owner": "DevOps",
      "status": "mitigated",
      "residual_risk": "low"
    },
    {
      "id": "RISK-003",
      "description": "PCI compliance audit delays production launch",
      "category": "compliance",
      "likelihood": "medium",
      "impact": "high",
      "severity_score": 8,
      "mitigation": {
        "strategy": "Start audit 2 weeks before target launch",
        "implementation": "Pre-audit checklist, security team engaged early",
        "verification": "Audit scheduled, checklist 90% complete"
      },
      "owner": "Security Team",
      "status": "in_progress",
      "residual_risk": "medium"
    }
  ]
}
```

## Risk Severity Matrix

| Likelihood/Impact | Low (1-3) | Medium (4-6) | High (7-9) | Critical (10) |
|-------------------|-----------|--------------|------------|---------------|
| **High (75%+)** | 3 | 6 | 9 | 10 |
| **Medium (25-75%)** | 2 | 5 | 8 | 9 |
| **Low (<25%)** | 1 | 3 | 7 | 8 |

**Severity Score = (Likelihood × Impact) / 2**

## Mitigation Strategies

1. **Avoid:** Change design to eliminate risk
2. **Mitigate:** Reduce likelihood or impact
3. **Transfer:** Use third-party service
4. **Accept:** Document and monitor

**Example:** RISK-001 → Mitigate (circuit breaker + fallback)
