# Day 11: Shared Infrastructure Integration

## Architecture Vision with Shared Infra Constraints

```markdown
# EP23 Payment Service - Infrastructure Integration

## Shared Services Integration

### MongoDB (shared-mongo:27017)
**Collections:**
- `payments`: Transaction records
- `audit_logs`: PCI compliance trail

**Indexes:** 
```javascript
db.payments.createIndex({transaction_id: 1}, {unique: true})
db.payments.createIndex({status: 1, created_at: -1})
```

### Prometheus Metrics
**Endpoint:** `GET /metrics`  
**Metrics:**
```
payment_transactions_total{provider="stripe",status="success"} 1234
payment_processing_duration_seconds{quantile="0.95"} 1.8
payment_provider_health{provider="stripe"} 1
```

### Grafana Dashboard
**Template:** `grafana/dashboards/payment_service.json`  
**Panels:** Transaction Rate, Latency (p50/p95/p99), Error Rate, Provider Health

### Loki Structured Logs
```json
{
  "timestamp": "2025-11-15T14:30:00Z",
  "level": "INFO",
  "service": "payment-service",
  "trace_id": "abc123",
  "message": "Payment processed successfully",
  "transaction_id": "txn_xyz"
}
```

## Constraints
- ✅ Must use shared MongoDB (no separate DB)
- ✅ Must expose /metrics and /health endpoints
- ✅ Must emit JSON structured logs
- ✅ Must use standard Grafana dashboard template

**Status:** Integrated with shared infrastructure baseline (Day 11)
```

**Time Saved:** 2 hours (no infrastructure setup needed)  
**Consistency:** All services follow same monitoring patterns
