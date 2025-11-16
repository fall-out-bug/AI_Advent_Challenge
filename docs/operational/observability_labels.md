# Observability Labels & Metrics · Epic 23

This document tracks Prometheus metrics introduced for Day 23 observability tasks. Where possible we align labels across runtimes (MCP HTTP API, Butler bot sidecar, CLI) so that dashboards and alerts can reuse the same selectors.

## Metrics

| Metric | Labels | Description | Emitted From |
| --- | --- | --- | --- |
| `benchmark_export_duration_seconds` | `exporter` (`digests`, `review_reports`) | Histogram of dataset export duration (scripts in `scripts/quality/analysis/`). | Export CLI, CI jobs. |
| `shared_infra_bootstrap_status` | `step` (`mongo`, `mock_services`) | Gauge (0/1) indicating whether CI bootstrap steps succeeded. | `scripts/ci/bootstrap_shared_infra.py`. |
| `structured_logs_total` | `service`, `level` | Counter of structured log entries emitted by any component. | `src/infrastructure/logging/__init__.py`. |
| `rag_variance_ratio` | `window` (`current`) | Gauge capturing variance of reranker scores for RAG++ (owner-only). | `src/infrastructure/rag/llm_reranker_adapter.py`. |
| `rag_rerank_score_variance` | n/a | Existing histogram (kept for backwards compatibility) – still recorded alongside `rag_variance_ratio`. | RAG reranker adapter. |
| `mcp_requests_total` | `tool`, `status` (`success`, `error`) | Counter of MCP tool invocations. | `src/infrastructure/monitoring/mcp_metrics.py`, `src/presentation/mcp/http_server.py`. |
| `mcp_request_duration_seconds` | `tool` | Histogram of MCP tool invocation latency. | `src/infrastructure/monitoring/mcp_metrics.py`. |
| `mcp_tools_registered` | n/a | Gauge tracking number of registered MCP tools. | `src/infrastructure/monitoring/mcp_metrics.py`, `src/presentation/mcp/server.py`. |
| `mcp_client_requests_total` | `tool`, `status` (`success`, `error`) | Counter of MCP client requests (used by RobustMCPClient). | `src/infrastructure/monitoring/agent_metrics.py`, `src/infrastructure/clients/mcp_client_robust.py`. |
| `mcp_client_retries_total` | `tool`, `reason` (`timeout`, etc.) | Counter of MCP client retries. | `src/infrastructure/monitoring/agent_metrics.py`, `src/infrastructure/clients/mcp_client_robust.py`. |
| `mcp_client_request_duration_seconds` | `tool` | Histogram of MCP client request latency. | `src/infrastructure/monitoring/agent_metrics.py`. |

## Registry & Endpoints

- **Unified registry:** All Prometheus metrics now use the default global `REGISTRY` from `prometheus_client`. Butler-specific collectors still expose convenience wrappers (`ButlerMetrics`) but share the same registry.
- **MCP HTTP server (`/metrics`):** continues to serve metrics via `src/presentation/mcp/http_server.py`, pulling directly from the shared registry.
- **Butler bot sidecar (`metrics_server.py`):** also emits the shared registry instead of a private collector. If the registry is unavailable, `/metrics` responds with HTTP 503.
- **Backoffice CLI:** instrumentation functions in `backoffice/metrics/prometheus.py` stay unchanged; they automatically register commands in the shared registry.

## Label Usage Guidance

1. **`exporter`** – differentiate between digest and reviewer pipelines; add more values if new exporters appear (e.g., `audit_log`).  
2. **`step`** – reserved for infrastructure bootstrap stages (Mongo, mock services, future additions such as `prometheus`, `grafana`).  
3. **`service`** – usually the logger name (`__name__` of module). When grouping dashboards, treat top-level package (e.g., `src.presentation.bot`) as the service key.  
4. **`window`** – for variance gauges; start with `current`, add `rolling_5m` etc. once RAG++ owner-only metrics expand.  
5. **`tool`** – MCP tool name (canonical label name for all MCP-related metrics). Use lowercase, snake_case tool names (e.g., `get_channel_digest`, `add_channel`).  
6. **`status`** – operation outcome for MCP/agent metrics. Use lowercase values: `success`, `error` (avoid `Success`, `Error`, `failed`, etc.).  
7. **`reason`** – retry/failure reason for MCP client metrics. Use lowercase values: `timeout`, `connection_error`, etc.  
8. **Structured logging:** include `level` label values in lowercase (`info`, `warning`, `error`, etc.) to simplify aggregation.

## Dashboards & Alerts

- Grafana: update/extend `grafana/dashboards/stage05-benchmarks.json` and `rag_variance.json` to plot the new metrics.  
- Alerts: integrate `shared_infra_bootstrap_status{step="mongo"} == 0` as CI pre-flight check; treat `rag_variance_ratio` > configured threshold as owner-only warning.

## Future Work

- Add latency histograms for `/metrics` endpoints once Day 23 observability stabilization completes.  
- Track log volume per component vs `structured_logs_total` for noise reduction.


