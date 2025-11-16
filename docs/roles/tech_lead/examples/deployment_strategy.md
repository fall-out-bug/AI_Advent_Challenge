# Deployment Strategy: Canary Rollout

## EP23 Payment Service - Production Deployment

### Canary Deployment Stages

```yaml
deployment_strategy: canary
rollout_phases:
  - name: "Canary 10%"
    replicas: 1/10
    duration: 1 hour
    success_criteria:
      error_rate: < 1%
      latency_p95: < 2s
      transaction_success_rate: > 99%
    rollback_trigger: Any criteria violated
    
  - name: "Canary 50%"
    replicas: 5/10
    duration: 2 hours
    success_criteria:
      error_rate: < 0.5%
      latency_p95: < 2s
      transaction_success_rate: > 99.5%
    rollback_trigger: Any criteria violated
    
  - name: "Full Production"
    replicas: 10/10
    duration: continuous
    success_criteria:
      error_rate: < 0.5%
      latency_p95: < 2s
    rollback_window: 24 hours

monitoring:
  metrics:
    - payment_transactions_total
    - payment_errors_total
    - payment_processing_duration_seconds
  alerts:
    - condition: error_rate > 1%
      action: Auto-rollback
      notification: PagerDuty + Slack
    - condition: latency_p95 > 3s
      action: Alert only (manual decision)
      notification: Slack

rollback:
  automated: true
  trigger: error_rate > 1% OR latency_p95 > 5s
  command: kubectl rollout undo deployment/payment-service
  duration: < 5 minutes
  verification: Previous version serving 100% traffic
```

### Rollout Timeline

```
14:00 - Deploy Canary 10% (1 replica)
        Monitor: error_rate, latency, transaction_success
15:00 - ✅ Success criteria met → Deploy Canary 50% (5 replicas)
17:00 - ✅ Success criteria met → Deploy Full (10 replicas)
17:05 - Production deployment complete
        24h monitoring window begins
```

### Rollback Scenarios

**Scenario A: High Error Rate**
- Trigger: error_rate > 1% for 5 minutes
- Action: Auto-rollback via Prometheus alert
- Command: `kubectl rollout undo deployment/payment-service`
- Duration: < 5 minutes
- Verification: Error rate returns to baseline

**Scenario B: Performance Degradation**
- Trigger: latency_p95 > 5s for 10 minutes
- Action: Manual rollback decision
- Notification: Slack alert to on-call
- Command: `kubectl rollout undo deployment/payment-service`

### Blue-Green Alternative

```yaml
# If canary not suitable (e.g., database schema changes)
deployment_strategy: blue_green
phases:
  - name: "Deploy Green"
    environment: production-green
    traffic: 0%
    
  - name: "Smoke Tests"
    tests: Critical path validation
    duration: 30 minutes
    
  - name: "Switch Traffic"
    from: production-blue
    to: production-green
    traffic: 100%
    duration: Instant switch
    
  - name: "Monitor"
    duration: 1 hour
    rollback: Switch back to blue if issues
```

**When to Use:**
- Canary: Gradual rollout, safe for most deploys
- Blue-Green: Instant switch, good for major releases with schema changes
