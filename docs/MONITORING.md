# Monitoring Documentation

## Overview

This document describes the monitoring setup, Grafana dashboards, and Prometheus metrics for the AI Challenge project.

## Architecture

### Components

- **Prometheus**: Metrics collection and storage (port 9090)
- **Grafana**: Metrics visualization and dashboards (port 3000)
- **Services**: Export metrics via `/metrics` endpoints

### Access

- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3000
- **Default Credentials**: admin/admin (change in production!)

## Starting Monitoring Stack

```bash
# Start all services including Prometheus and Grafana
docker-compose -f docker-compose.day12.yml up -d

# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health
```

## Prometheus Configuration

### Metrics Endpoints

Prometheus scrapes metrics from:

- `mcp-server:8004/metrics` - MCP server metrics
- `mistral-chat:8000/metrics` - LLM model metrics
- `telegram-bot:8000/metrics` - Bot metrics (if exposed)
- `summary-worker:8000/metrics` - Worker metrics (if exposed)
- `post-fetcher-worker:8000/metrics` - Post fetcher metrics (if exposed)

### Configuration Files

- `prometheus/prometheus.yml` - Main Prometheus config
- `prometheus/alerts.yml` - Alert rules

### Retention

- **Data retention**: 30 days
- **Storage**: Docker volume `prometheus_data`

## Grafana Dashboards

### Dashboard 1: App Health

**Location**: `grafana/dashboards/app-health.json`

**Panels**:
- System Resources: CPU, Memory, Restarts
- HTTP Metrics: Status codes (2xx/4xx/5xx), Request rate, Error rate
- Latency: P50, P95, P99 response times
- Availability: Uptime, SLA status

**Access**: Grafana → Dashboards → App Health

### Dashboard 2: ML Service Metrics

**Location**: `grafana/dashboards/ml-service-metrics.json`

**Panels**:
- Model Performance: Latency P50/P95/P99
- Request Volume: Predictions/min, Token generation rate
- Errors: Error rate by type, Exception rate
- Model Quality: Quality score, Summarization length
- Model Metadata: Version, Hash, Last updated
- Drift Detection: Response length changes, Latency drift

**Access**: Grafana → Dashboards → ML Service Metrics

### Dashboard 3: Post Fetcher & PDF Metrics

**Location**: `grafana/dashboards/post-pdf-metrics.json`

**Panels**:
- Post Fetcher: Posts saved/skipped, Channels processed, Duration
- PDF Generation: Duration, File size, Pages, Errors
- Bot Digest: Requests, Cache hits/rate, Errors

**Access**: Grafana → Dashboards → Post Fetcher & PDF Metrics

### Dashboard 4: Review Pipeline SLOs

**Location**: `grafana/dashboards/slo-review-pipeline.json`

**Panels**:
- Pipeline latency vs. 5 minute SLO target
- Unified worker success rate stat panel
- Code review backlog depth gauge

### Dashboard 5: MCP Server SLOs

**Location**: `grafana/dashboards/slo-mcp-server.json`

**Panels**:
- MCP request error rate vs. threshold
- Request P95 latency with SLO target overlay
- Overall request throughput

### Dashboard 6: Butler Bot SLOs

**Location**: `grafana/dashboards/slo-butler-bot.json`

**Panels**:
- Butler bot error rate vs. 10% threshold
- Message processing P95 latency vs. 5 second target
- Messages per minute indicator

## Adding Custom Panels

1. Open Grafana UI: http://localhost:3000
2. Navigate to dashboard
3. Click "Edit" (pencil icon)
4. Add panel → Choose visualization type
5. Configure query (PromQL)
6. Save dashboard

## Prometheus Alerts

### Alert Groups

1. **day12_alerts**: Day 12 specific alerts (post fetcher, PDF generation, bot digest)
2. **ml_alerts**: ML/LLM service alerts (latency, errors, drift)

### Key Alerts

- **HighLLMLatency**: P95 latency > 5s for 5 minutes
- **HighLLMErrorRate**: Error rate > 10% for 2 minutes
- **LLMModelDown**: Model service unavailable > 2 minutes
- **LLMModelDrift**: Latency drift detected
- **PDFGenerationHighErrorRate**: Error rate > 10%
- **PostFetcherWorkerDown**: Worker stopped > 2 minutes

### Alert Configuration

Alerts are defined in `prometheus/alerts.yml`. To add new alerts:

1. Edit `prometheus/alerts.yml`
2. Add alert rule to appropriate group
3. Restart Prometheus: `docker-compose restart prometheus`

## Log Aggregation (Loki + Promtail)

- **Loki**: collects application logs exposed by Docker containers (port 3100)
- **Promtail**: ships container logs to Loki; configured via
  `promtail/promtail-config.yml`
- **Grafana integration**: Loki datasource provisioned automatically
  (`grafana/provisioning/datasources/prometheus.yml`)

### Common LogQL Queries

```logql
{stream="audit"} | json | line_format "{.action} {.resource} {.outcome}"

{service="unified-task-worker"} | json | level!="INFO"

count_over_time({service="mcp-server"} |= "ERROR" [5m])
```

### Retention
- Loki filesystem storage retains logs for 30 days (`loki/loki-config.yml`).
- Audit events are tagged with `stream="audit"` for longer retention policies.

## Metrics Exposed

### Post Fetcher Worker

- `post_fetcher_posts_saved_total` - Total posts saved
- `post_fetcher_posts_skipped_total` - Duplicate posts skipped
- `post_fetcher_channels_processed_total` - Channels processed
- `post_fetcher_duration_seconds` - Processing duration histogram
- `post_fetcher_errors_total` - Errors by type
- `post_fetcher_worker_running` - Worker running status

### PDF Generation

- `pdf_generation_duration_seconds` - Generation duration histogram
- `pdf_generation_errors_total` - Errors by type
- `pdf_file_size_bytes` - File size histogram
- `pdf_pages_total` - Page count histogram

### Bot Digest

- `bot_digest_requests_total` - Total requests
- `bot_digest_cache_hits_total` - Cache hits
- `bot_digest_errors_total` - Errors by type

### ML Metrics (Future)

- `llm_inference_latency_seconds` - LLM inference latency
- `llm_token_generation_rate_total` - Tokens generated
- `llm_model_version` - Model version
- `llm_error_rate_total` - Errors by type
- `llm_request_token_count` - Token count histogram

## Querying Metrics

### Using Prometheus UI

1. Open http://localhost:9090
2. Go to "Graph" tab
3. Enter PromQL query
4. View results

### Example Queries

```promql
# Request rate per second
sum(rate(http_requests_total[5m]))

# Error rate percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# LLM inference latency P95
histogram_quantile(0.95, rate(llm_inference_latency_seconds_bucket[5m]))
```

## Troubleshooting

### Prometheus not scraping

1. Check service is running: `docker-compose ps`
2. Check metrics endpoint: `curl http://localhost:8004/metrics`
3. Check Prometheus targets: http://localhost:9090/targets
4. Check Prometheus logs: `docker logs prometheus-day12`

### Grafana dashboards not loading

1. Check datasource: Grafana → Configuration → Data Sources → Prometheus
2. Test connection: Click "Test" button
3. Check dashboard JSON format: Validate JSON syntax
4. Check Grafana logs: `docker logs grafana-day12`

### Metrics not appearing

1. Verify service exposes `/metrics` endpoint
2. Check Prometheus scrape config includes service
3. Check service labels match Prometheus config
4. Wait for scrape interval (30s default)

## Production Considerations

1. **Change default passwords**: Set `GRAFANA_ADMIN_PASSWORD` in `.env`
2. **Enable authentication**: Configure Grafana auth providers
3. **Network security**: Restrict access to monitoring ports
4. **Retention policy**: Adjust based on storage capacity
5. **Alert notifications**: Configure Alertmanager for Slack/email/PagerDuty
6. **Backup**: Backup Prometheus data volume regularly

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)

