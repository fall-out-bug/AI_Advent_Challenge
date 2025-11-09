# Test Baseline (Before Shared Infra Migration)

> Date: 2025-11-07

## Commands Executed

```bash
poetry run pytest tests/ -v
poetry run pytest tests/e2e/test_review_pipeline.py --benchmark-only  # fails: plugin not installed
```
- Benchmark command fails because `pytest-benchmark` is not available in the
  environment (`--benchmark-only` argument unknown).

## Observations

- Test collection fails because optional third-party stacks (Airflow, Telegram bot, etc.)
  are not installed in the current environment.
- Additional import mismatches exist between integration and unit test modules that
  share identical filenames (e.g. `test_mistral_orchestrator`).

### Notable Errors

| Issue | Affected Tests |
|-------|----------------|
| `IndentationError` in fixture expectations | `tests/e2e/test_digest_pdf_button.py` |
| Missing optional dependency `airflow` | `tests/fixtures/airflow_only/dags/test_dag.py` |
| Bot handler import mismatch (`menu_router`) | `tests/presentation/bot/test_menu_handlers.py` |
| Duplicate module names between integration/unit suites | `tests/unit/application/test_mistral_orchestrator.py`, `tests/unit/infrastructure/llm/test_token_counter.py`, `tests/unit/presentation/bot/handlers/test_butler_handler.py` |
| Namespace packages shadowed by dependency modules (e.g. `intent.*`) | Multiple `tests/unit/intent/*` |
| Missing generated adapter fixtures | `tests/unit/presentation/mcp/test_formalize_adapter.py` |

## Next Steps

- Limit baseline runs to critical smoke suites (e.g. `tests/unit/domain`, `tests/unit/application`) until optional dependencies are provisioned.
- Introduce namespace-safe package initialisers to avoid conflicts with dependency test modules (partially addressed by `tests/__init__.py`).
- Provision or mock optional services (Airflow, Telegram bot, MCP adapters) for consistent CI runs.
### 2025-11-07 Smoke Test (Shared Infra)
- Command: `docker run --network infra_infra_app-network ... poetry run python scripts/test_review_system.py`
- Result: All 5 checks passed (MongoDB, archive extraction, diff analysis, use cases, full pipeline).
- Notes: External API mock used; tasks `rev_114563a41ab8` and `rev_cde6b2c9e1e3` queued and succeeded in shared MongoDB.

