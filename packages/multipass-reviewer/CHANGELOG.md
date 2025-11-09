# Changelog

## 0.1.0 - 2025-11-07
- Initial package scaffolding (Clean Architecture layout, tooling config).

## 0.2.0 - 2025-11-08
- Shared-infra ready orchestrator with `ReviewConfigBuilder` presets and DI-first wiring.
- Async architecture/component/synthesis passes exposed through clean interfaces.
- Checker suite: lint, type hints, Python style, Spark/Airflow, MLOps/Data, Haiku.
- Prometheus metrics helpers for checker findings, runtimes, and LLM token/latency tracking.
- Tenacity-based retry policy for all LLM requests with exponential backoff.
- Graceful degradation when passes or LLM synthesis fail (partial reports with error metadata).
- Integration tests and strict lint/type coverage (mypy, flake8, black, isort).
- Package README and API docs refreshed for Docker/REST distribution.
