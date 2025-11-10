# EP04 Archive · Scripts

Store deprecated automation or helper scripts here. Capture prerequisites, expected environment variables, and the modern workflow that supersedes each script.

## Archived on 2025-11-09

- `start_models.sh` — replaced by `make day-12-up`
- `wait_for_model.sh` — readiness handled by shared infra
- `check_model_status.sh` — use `scripts/test_review_system.py --metrics`
- `ci/test_day10.sh` — superseded by updated CI pipelines
- `day12_run.py` — replaced by make targets and CLI backoffice commands
- `mcp_comprehensive_demo.py` — use updated MCP demos in docs
- `healthcheck_mcp.py` — consolidated into review system test script
- `telegram_channel_reader.session` — removed (sensitive session)
