# Day 12: Deployment Topology Design

## Multi-Environment Deployment Architecture

```markdown
# EP23 Payment Service - Deployment Topology

## Environment Matrix

| Environment | Platform | Replicas | CPU/Memory | Database | Secrets |
|------------|----------|----------|------------|----------|---------|
| Local | Docker Compose | 1 | 1 CPU, 512MB | MongoDB container | .env file |
| Staging | K8s (GKE) | 3 | 2 CPU, 1GB | Shared cluster | K8s Secrets |
| Production | K8s (GKE) | 10 | 4 CPU, 2GB | Dedicated cluster | K8s Secrets |

## Health Checks

### Liveness Probe (`/health`)
```yaml
livenessProbe:
  httpGet: {path: /health, port: 8080}
  initialDelaySeconds: 10
  periodSeconds: 30
  failureThreshold: 3
```
Returns: `{"status": "ok", "uptime": 3600}`

### Readiness Probe (`/ready`)
```yaml
readinessProbe:
  httpGet: {path: /ready, port: 8080}
  initialDelaySeconds: 5
  periodSeconds: 10
```
Returns: `{"status": "ready", "dependencies": {"mongodb": "ok", "stripe": "ok"}}`

## Startup Sequence
1. MongoDB starts → wait for ready
2. Payment Service starts → connect to MongoDB
3. Health checks pass → service ready
4. Load Balancer adds to pool

## Rollout Strategy
- **Staging:** Rolling update (1 replica at a time)
- **Production:** Canary (10% → 50% → 100%)
- **Rollback:** Previous version kept for 24h

**Deployment Time:** 5 minutes (staging), 15 minutes (production canary)
```
