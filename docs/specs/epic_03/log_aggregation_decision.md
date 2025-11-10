# Log Aggregation Solution Decision (Stage 03_02)

## Context
Stage 03_02 requires a unified log aggregation platform to support the new
structured logging pipeline, enable cross-service investigations, and feed SLO
dashboards. The existing setup relies on per-container stdout scraping, which
is insufficient for correlating incidents across MCP, workers, and the Butler
bot.

## Options Evaluated

### Grafana Loki
- **Pros**: Native integration with existing Grafana stack, simple operational
  footprint, multi-tenant labels align with contextual logging metadata,
  Promtail agent provides drop-in Docker support.
- **Cons**: Query language (LogQL) is less mature than Elasticsearch DSL;
  limited full-text search capabilities compared to ELK.
- **Integration Notes**: Requires Promtail sidecar for each service and Loki
  datasource configuration in Grafana.

### Elasticsearch / Logstash / Kibana (ELK)
- **Pros**: Rich query DSL, mature ecosystem, powerful full-text search and
  alerting.
- **Cons**: Operationally heavy; requires dedicated JVM resources, shard
  management, and index lifecycle tooling. Overkill for current log volumes.
- **Integration Notes**: Would necessitate Logstash or Filebeat agents and
  additional Terraform/state management to provision the cluster.

### Cloud Provider Managed Services
- **Pros**: Minimal upkeep if hosted (e.g., AWS CloudWatch, GCP Logging).
- **Cons**: Locks the deployment pipeline to a specific provider, complicates
  local development, and introduces additional cost monitoring.

## Decision
Adopt **Grafana Loki** with Promtail agents as the log aggregation solution for
Stage 03_02.

## Rationale
- Aligns with existing Grafana footprint, simplifying dashboard updates.
- Lightweight deployment that fits within the current docker-compose based
  infrastructure.
- Labels map directly to the structured logging context (request_id, user_id,
  service), improving query ergonomics.

## Follow-up Actions
1. Provision Loki and Promtail services in `docker-compose.butler.yml` (tracked
   in TODO `todo-1762671602154-tx4i6gd7p`).
2. Update Grafana provisioning to add Loki datasource.
3. Document common LogQL queries in `docs/reference/en/MONITORING.md`.
