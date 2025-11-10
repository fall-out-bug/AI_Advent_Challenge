# EP03 Risk Register

| ID | Risk Description | Impact | Likelihood | Mitigation / Next Step | Owner | Status |
|----|------------------|--------|------------|------------------------|-------|--------|
| R1 | Critical flows (review pipeline, unified worker, MCP) emit no Prometheus metrics or scrape targets, leaving incidents undetected. | High – review SLAs cannot be measured or enforced. | High | Stage 03_02 to add exporters and scrape configs for all production services; ship regression tests for `/metrics`. | EP03 Tech Lead | Open |
| R2 | Prometheus alert rules rely on metrics that are not emitted (`mcp_requests_total`, `llm_error_rate_total`, `http_requests_total`), so on-call never receives actionable alerts. | High – silent failures in MCP and LLM layers. | Medium | Replace alerts with validated metrics during Stage 03_02; add PromQL lint checks to CI. | EP03 Tech Lead | Open |
| R3 | Absence of centralized log aggregation (Loki/ELK) prevents investigations beyond container logs. | Medium – increases MTTR during incidents. | Medium | Select aggregation stack in Stage 03_02, enforce structured logging keys (request_id, user_id). | EP03 & Ops leads | Open |
| R4 | No automated observability verification in CI/CD; regressions in dashboards, metrics, or alerts will ship unnoticed. | Medium – instrumentation debt accumulates. | High | Introduce GitHub Actions to run `promtool check rules`, dashboard lint, and smoke probes before deploy. | DevOps | Open |
| R5 | Compliance posture unclear (audit logging, PII masking), risking future governance blockers. | Medium – delays production approval. | Medium | Document minimum audit logging requirements and align with security guidance in Stage 03_02. | Security Lead | Open |

