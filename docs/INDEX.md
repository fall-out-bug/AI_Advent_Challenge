# AI Challenge Documentation Index

## Guides

### English
- [Development & Deployment](guides/en/DEVELOPMENT.md)
- [User Guide](guides/en/USER_GUIDE.md)
- [Troubleshooting](guides/en/TROUBLESHOOTING.md)
- [Deployment Playbooks](guides/en/DEPLOYMENT.md)
- [Maintainer Playbook](MAINTAINERS_GUIDE.md)
- [Shared Infra Cutover](guides/en/shared_infra_cutover.md)
- [Observability Operations Guide](guides/en/observability_operations_guide.md)
- [Telegram Setup](guides/en/telegram_setup.md) · [Cache Guide](guides/en/telegram_agent_cache.md)
- [MCP Demo Guide](guides/en/MCP_DEMO_GUIDE.md)
- [MCP Homework Review](guides/en/MCP_HOMEWORK_REVIEW.md)
- [MCP Tool Usage](guides/en/MCP_TOOL_USAGE.md)
- [Migration Guide](guides/en/MIGRATION_GUIDE.md)
- [Modular Reviewer Integration](guides/en/MODULAR_REVIEWER_INTEGRATION_GUIDE.md)
- [Agent Integration (EN)](guides/en/AGENT_INTEGRATION.md)

### Russian
- [Agent Integration (RU)](guides/ru/AGENT_INTEGRATION.ru.md)
- [Modular Reviewer Integration (RU)](guides/ru/MODULAR_REVIEWER_INTEGRATION_GUIDE.ru.md)

## Reference

### Architecture & Design
- [Architecture Overview](reference/en/ARCHITECTURE.md)
- [Architecture FSM](reference/en/ARCHITECTURE_FSM.md)
- [Review System Architecture](reference/en/review_system_architecture.md)
- [Component Detection Strategy](reference/en/COMPONENT_DETECTION_STRATEGY.md)
- [Context Compression Strategy](reference/en/CONTEXT_COMPRESSION_STRATEGY.md)
- [Token Management Strategy](reference/en/TOKEN_MANAGEMENT_STRATEGY.md)
- [Multi-Pass Architecture](reference/en/MULTI_PASS_ARCHITECTURE.md)
- [Reviewer Dependency Audit](reference/en/reviewer_dependency_audit.md)
- Architecture research notes: [Prompt Tuning](reference/architecture/mcp_agent_prompt_tuning_report.md), [Summarisation State](reference/architecture/SUMMARIZATION_CURRENT_STATE.md)

### API & Contract Docs
- [API Overview](reference/en/API.md)
- [MCP API](reference/en/API_MCP.md)
- [MCP Tool Catalog](reference/en/API_MCP_TOOLS.md)
- [Reviewer API](reference/en/API_REVIEWER.md)
- [Bot Backoffice API](reference/en/API_BOT_BACKOFFICE.md)
- Russian translations: [MCP API (RU)](reference/ru/API_MCP.ru.md), [Bot Backoffice API (RU)](reference/ru/API_BOT_BACKOFFICE.ru.md), [Reviewer API (RU)](reference/ru/API_REVIEWER.ru.md)
- [Technical Design (RU)](reference/ru/TECHNICAL_DESIGN.ru.md)

### Testing & Quality
- [Testing Strategy](reference/en/TESTING.md)
- [Testing Fixtures Guide](reference/en/TESTING_FIXTURES_GUIDE.md)
- [Test Baseline](reference/en/test_baseline.md)
- [Testing the Review System](reference/en/testing_review_system.md)
- [Audit Report](reference/en/AUDIT_REPORT_CODE_REVIEW.md)

### Monitoring & Operations
- [Monitoring Guide](reference/en/MONITORING.md)
- [ML Monitoring](reference/en/ML_MONITORING.md)
- [Security Policies](reference/en/SECURITY.md)
- [MongoDB Notes](reference/en/mongodb-warnings.md)
- [Model Setup](reference/en/MODEL_SETUP.md)
- [Performance Benchmarks](reference/en/PERFORMANCE_BENCHMARKS.md)
- [Operations FAQ](reference/operations/MISTRAL_NO_REBUILD.md)

## Specs & Program Tracking
- [Architecture Specification](specs/architecture.md)
- [System Specification](specs/specs.md)
- [Operations Guide](specs/operations.md)
- [Progress Tracker](specs/progress.md)
- Epic folders: `specs/epic_00` … `specs/epic_06`, `specs/epic_19`, `specs/epic_23`

## Scripts & Automation
- Infrastructure helpers: `../scripts/infra/`
- Maintenance utilities: `../scripts/maintenance/`
- Quality & benchmarks: `../scripts/quality/`
- Legacy demos and archives: `../archive/legacy/2023-day12/`

## Archives & History
- Archived documents: `docs/archive/`
- Release notes: `docs/archive/release_notes/`
- Legacy day-11 quick start: `docs/archive/2023-day11/`
- Phase 1–3 requirements & historical research under `docs/archive/`
- Full project changelog: [CHANGELOG.md](../CHANGELOG.md)

## Thematic Collections
- Day 15 (Quality & Fine-tuning): `docs/day15/`
- Day 12 (PDF Digest System): `docs/day12/`
- Day 17 (Code Review Platform): see `docs/reference/en/` + `docs/specs/epic_05/`
- AI assistant context files: [AI_CONTEXT.md](../AI_CONTEXT.md), [.cursorrules](../.cursorrules)

---

Need something else? Review the [Maintainer Playbook](MAINTAINERS_GUIDE.md) or the Stage 06 specs for ongoing cleanup notes.
