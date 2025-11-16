# Shared Infra Restart Validation · Epic 23 (TL-05)

## 1. Context
- **Date:** 2025-11-16
- **Engineer:** dev_a
- **Goal:** Prove that the shared CI stack (Mongo + mock LLM/Prometheus) can be bootstrapped and shut down cleanly, emitting Day 23 observability metrics.

## 2. Commands Executed
```bash
# Bootstrap shared infra on non-default ports to avoid collisions
python scripts/ci/bootstrap_shared_infra.py --mongo-port 49017 --mock-port 29080

# Validate containers / services (excerpt)
docker ps --filter "name=ai-challenge-ci-mongo" --format "{{.Names}} {{.Status}}"
docker ps --filter "name=mock_shared_services" --format "{{.Names}} {{.Status}}"

# Tear down stack
python scripts/ci/cleanup_shared_infra.py
```

## 3. Observability Evidence
- `shared_infra_bootstrap_status{step="mongo"}` and `{step="mock_services"}` gauges flipped to `1` during bootstrap, confirmed via `/metrics` scrape in the CI logs (exposed by the bootstrap script).
- PromQL snippets used:
  - `shared_infra_bootstrap_status`
  - `up{job="mongo"}`
- Loki query (tail) to confirm no lingering errors: `{container="ai-challenge-ci-mongo"} | json`.

## 4. Outcome
- Bootstrap completed successfully (no stderr output, containers briefly registered in `docker ps`).
- Cleanup script removed the containers; subsequent `docker ps` showed no `ai-challenge-ci-mongo`.
- Metrics emitted into Prometheus registry for CI to pick up (available via `benchmark-dataset-audit` artifact in workflow run).

## 5. Follow-ups
- ✅ Implemented `make day-23-up/down` wrappers around the bootstrap/cleanup scripts for local developers (completed 2025-11-16).
- Wire the PromQL/Loki checks into GitHub Actions for automated evidence capture (shared_infra_bootstrap_status already exported).
- Added `--check` flag to `bootstrap_shared_infra.py` for CI gating (TL-05 DoD).
- Created integration tests in `tests/integration/shared_infra/test_bootstrap.py` to verify bootstrap/cleanup/restart flows.
