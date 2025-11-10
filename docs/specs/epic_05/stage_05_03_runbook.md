# Stage 05_03 Runbook · Fine-Tuning Execution & Operations

## 1. Preparation
- Load shared infra credentials (`source ~/work/infra/.env.infra`).
- Verify access to Stage 05 datasets (see `stage_05_03_pilot.md`).
- Confirm Qwen fine-tuning environment is available (GPU node or distributed job).

## 2. Launch Fine-Tuning
1. Checkout repo commit referenced in pilot plan.
2. Activate environment (e.g., `poetry shell`).
3. Run training command (example):
   ```bash
   python scripts/finetune/run_finetune.py \
     --config configs/finetune/qwen_ru_digest.yaml \
     --dataset data/benchmarks/benchmark_digest_ru_v1/2025-11-09_samples.jsonl \
     --output models/qwen-7b-ft-ru-digest-stage05
   ```
4. Capture logs and metrics; store output artefacts under configured registry.

## 3. Validation
1. Execute benchmark:
   ```bash
   python scripts/benchmark/run_benchmark.py \
     --scenario channel_digest_ru \
     --dataset data/benchmarks/benchmark_digest_ru_v1/2025-11-09_samples.jsonl \
     --fail-on-warn
   ```
2. Record metrics vs baseline table.
3. Conduct manual QA on 5 samples focusing on coverage and factual accuracy.

## 4. Deployment & Release Alignment
- Deploy new model only during main product release window.
- Notify operations with evaluation summary and go/no-go decision.

## 5. Rollback Procedure
- Maintain baseline model pointer (`qwen-7b`).
- To revert: update deployment config to previous model, flush caches, rerun
  benchmark to confirm recovery.
- Document rollback in incident log.

## 6. Monitoring & Alerts
- Ensure Prometheus job scrapes fine-tuned model metrics (latency, drift).
- Import/refresh Grafana dashboards (`grafana/dashboards/stage05-benchmarks.json`).
- Configure alert thresholds per governance policy.

## 7. Documentation & Sign-off
- Update `stage_05_03_pilot.md` with run details and results.
- Capture approval outcomes in `docs/specs/epic_05/stage_05_03_signoff.md`.
- Log lessons learned and backlog items for Epic 23 if data gaps remain.
