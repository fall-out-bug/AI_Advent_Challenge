# Troubleshooting Playbook

This guide lists common issues encountered when running the modular multipass
reviewer on shared infrastructure and how to resolve them.

## 1. Connectivity

| Symptom | Investigation | Resolution |
| --- | --- | --- |
| `MongoDB unavailable` skip/Exception | `poetry run python tests/integration/shared_infra/test_shared_infra_connectivity.py::test_shared_mongo_connection` | Attach runner to `infra_infra_db-network`, export `MONGODB_USERNAME/PASSWORD`, or set `TEST_MONGODB_URL=mongodb://<user>:<pass>@shared-mongo:27017/ai_challenge_test?authSource=admin` |
| `llm-mistral-chat-1` timeout | `curl http://llm-mistral-chat-1:8000/health` from container | Verify container joined `infra_shared_network`; restart shared LLM service if unhealthy |
| Prometheus metrics missing | `curl http://localhost:8000/metrics` | Add scrape config for reviewer service in shared Prometheus; confirm `PROMETHEUS_URL` env var |

## 2. Review Pipeline Errors

| Error | Cause | Fix |
| --- | --- | --- |
| `Unknown model: summary` | Legacy unified client lacked alias mapping | Ensure latest `ModularReviewService` alias adapter is deployed; restart worker |
| `Input validation failed: model_name` | Model name contains suffix (`mistral-7b-...`) | Use alias (`mistral`, `qwen`, etc.) or rely on automatic normalisation |
| `TypeError: ... log_parser ... missing` | Outdated use case call signature | Update invocations to let `ReviewSubmissionUseCase` provide defaults |
| Review task stuck `pending` | Worker offline or Mongo queue issue | Check `unified-task-worker` logs, verify Mongo connection, restart worker |

## 3. Archive Handling

| Problem | Action |
| --- | --- |
| `413 Payload Too Large` when uploading archives | Increase `archive_max_total_size_mb` in settings or split submission |
| Temporary files not cleaned | Review archives stored in `review_archives/`; schedule cleanup job |

## 4. Test Failures

| Scenario | Cause | Resolution |
| --- | --- | --- |
| e2e tests skip due to Mongo | Test runner not on shared network OR missing credentials | Run tests inside a container attached к обоим внешним сетям и задайте `MONGODB_USERNAME/MONGODB_PASSWORD` (или `TEST_MONGODB_URL` с `authSource=admin`) |
| `pytest-asyncio` event loop mismatch | Mixed loop fixtures | Ensure `pytest.ini` sets `asyncio_mode = auto` (already default) and avoid creating loops manually |
| `ModuleNotFoundError: multipass_reviewer` | Package not on path | Set `PYTHONPATH=packages/multipass-reviewer` or install the package before running tests |

## 5. Observability

- Grafana: `http://shared-grafana:3000` → dashboards under *AI Challenge*
- Prometheus: `http://shared-prometheus:9090` → query
  `review_checker_findings_total`
- API metrics: `GET /metrics`

## 6. Support Checklist

1. Confirm `.env` variables mirror shared infra hostnames.
2. Validate Docker networks (run `docker network inspect` for both external
   networks).
3. Run shared infra integration tests.
4. Review worker logs (`docker compose -f docker-compose.butler.yml logs -f unified-task-worker`).
5. Capture metrics/health outputs when escalating.
